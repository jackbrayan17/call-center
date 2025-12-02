from django.contrib.auth import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import AuditLog, SessionSnapshot


def _get_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_session_key(request):
    try:
        if request and hasattr(request, "session"):
            key = request.session.session_key
            if not key:
                request.session.create()
                key = request.session.session_key
            return key or ""
    except Exception:
        return ""
    return ""


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    session_key = _get_session_key(request)
    ip_addr = _get_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "") if request else ""
    now = timezone.now()
    SessionSnapshot.objects.update_or_create(
        session_key=session_key,
        defaults={
            "user": user,
            "ip_address": ip_addr,
            "user_agent": ua[:1024],
            "login_at": now,
            "last_activity": now,
            "is_active": True,
        },
    )
    AuditLog.objects.create(
        user=user,
        session_key=session_key,
        ip_address=ip_addr,
        method="LOGIN",
        path="/login",
        status_code=200,
        user_agent=ua[:1024],
        duration_ms=0,
        payload_summary="user_logged_in",
    )


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    session_key = _get_session_key(request)
    ip_addr = _get_ip(request)
    ua = request.META.get("HTTP_USER_AGENT", "") if request else ""
    now = timezone.now()
    SessionSnapshot.objects.filter(session_key=session_key).update(
        is_active=False,
        last_activity=now,
    )
    AuditLog.objects.create(
        user=user if user.is_authenticated else None,
        session_key=session_key,
        ip_address=ip_addr,
        method="LOGOUT",
        path="/logout",
        status_code=200,
        user_agent=ua[:1024],
        duration_ms=0,
        payload_summary="user_logged_out",
    )
