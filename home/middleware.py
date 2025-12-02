from __future__ import annotations

import time
from typing import Optional

from django.utils import timezone

from .models import AuditLog, SessionSnapshot


class AuditLogMiddleware:
    """
    Enregistre les requêtes (user, IP, session, user-agent, URL, code, durée)
    et met à jour la dernière activité de la session.
    """

    _last_prune: Optional[float] = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()

        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            try:
                self._handle_after(request, response, start)
            except Exception:
                # Ne pas interrompre la requête en cas d'échec du log
                pass

    def _handle_after(self, request, response, start: float) -> None:
        path = request.path
        if path.startswith("/static/") or path.startswith("/media/"):
            return

        duration_ms = int((time.monotonic() - start) * 1000)
        user = getattr(request, "user", None)
        user_obj = user if user and user.is_authenticated else None
        session_key = ""
        try:
            session_key = request.session.session_key or ""
        except Exception:
            session_key = ""

        ip_addr = self._get_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        status_code = getattr(response, "status_code", 0) if response else 0
        payload_summary = self._summarize_payload(request)

        AuditLog.objects.create(
            user=user_obj,
            session_key=session_key,
            ip_address=ip_addr,
            method=request.method[:8],
            path=path,
            status_code=status_code,
            user_agent=user_agent[:1024],
            duration_ms=duration_ms,
            payload_summary=payload_summary[:4000],
        )

        # Maj activité session
        if session_key:
            SessionSnapshot.objects.update_or_create(
                session_key=session_key,
                defaults={
                    "user": user_obj,
                    "ip_address": ip_addr,
                    "user_agent": user_agent[:1024],
                    "last_activity": timezone.now(),
                    "login_at": timezone.now(),
                    "is_active": True,
                },
            )

        self._prune_old_logs()

    @staticmethod
    def _get_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def _summarize_payload(request) -> str:
        if request.method in ("POST", "PUT", "PATCH"):
            keys = list(request.POST.keys())
            return f"{request.method} keys={keys}"
        if request.GET:
            keys = list(request.GET.keys())
            return f"GET keys={keys}"
        return ""

    def _prune_old_logs(self):
        now = time.time()
        if self._last_prune and now - self._last_prune < 6 * 3600:
            return
        cutoff = timezone.now() - timezone.timedelta(days=90)
        AuditLog.objects.filter(created_at__lt=cutoff).delete()
        SessionSnapshot.objects.filter(last_activity__lt=cutoff).delete()
        self._last_prune = now
