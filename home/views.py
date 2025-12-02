import csv
import base64
import json
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .forms import CallRecordForm, ImportCompaniesForm
from .models import CallRecord, Company


def _user_cards():
    User = get_user_model()
    users = list(User.objects.all().order_by("username"))
    stats = {}
    calls = CallRecord.objects.select_related("user")
    for call in calls:
        if not call.user_id:
            continue
        stat = stats.setdefault(call.user_id, {"total": 0, "complete": 0, "incomplete": 0, "points": 0})
        stat["total"] += 1
        is_complete = (
            call.call_status == "accepted"
            and call.presentation_level
            and call.questions_libres_level
            and call.questions_orientees_level
        )
        if is_complete:
            stat["complete"] += 1
            stat["points"] += 2
        else:
            stat["incomplete"] += 1
            stat["points"] += 1

    max_points = max([s["points"] for s in stats.values()] or [1])
    user_cards = []
    for u in users:
        stat = stats.get(u.id, {"total": 0, "complete": 0, "incomplete": 0, "points": 0})
        points = stat["points"]
        user_cards.append(
            {
                "username": u.get_username(),
                "initial": (u.get_username()[:1] or "U").upper(),
                "total": stat["total"],
                "complete": stat["complete"],
                "incomplete": stat["incomplete"],
                "points": points,
                "ratio": int((points / max_points) * 100) if max_points else 0,
            }
        )
    user_cards.sort(key=lambda x: x["username"].lower())
    return user_cards


def _require_access(request: HttpRequest) -> bool:
    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour accéder aux appels.")
        return False
    return True


def _ensure_seed_data() -> None:
    if Company.objects.exists():
        return
    seed = [
        dict(name="Tech Horizon", phone="+33 6 11 22 33 44", product="SaaS", activity="Logiciels", location="Paris",
             legal_form="SARL", niu="FR1234567", validity_score=8.5),
        dict(name="AgriNova", phone="+33 6 55 66 77 88", product="AgriTech", activity="Agriculture", location="Lyon",
             legal_form="SAS", niu="FR9876543", validity_score=7.1),
        dict(name="EcoBuild", phone="+33 1 44 55 66 77", product="Construction", activity="BTP", location="Marseille",
             legal_form="SARL", niu="FR5558888", validity_score=6.4),
        dict(name="DataPulse", phone="+33 7 22 33 44 55", product="Data", activity="Analyse", location="Toulouse",
             legal_form="SAS", niu="FR2224444", validity_score=9.2),
    ]
    Company.objects.bulk_create(Company(**row) for row in seed)


def home(request: HttpRequest) -> HttpResponse:
    """Landing page."""
    user_cards = _user_cards()
    return render(request, "home/index.html", {"user_cards": user_cards})


def dashboard(request: HttpRequest) -> HttpResponse:
    _ensure_seed_data()
    total_companies = Company.objects.count()
    status_counts = Company.objects.values("status").annotate(total=Count("id"))
    status_map = {row["status"]: row["total"] for row in status_counts}
    success_calls = CallRecord.objects.filter(call_status="accepted")
    calls_by_status = success_calls.values("status_numero").annotate(total=Count("id"))
    answered = sum(row["total"] for row in calls_by_status if row["status_numero"] == "answered")
    product_counts = (
        success_calls.values("company__product")
        .annotate(total=Count("id"))
        .order_by("company__product")
    )
    calls_with_audio = success_calls.filter(recordings__isnull=False).distinct().count()
    calls_without_audio = success_calls.filter(recordings__isnull=True).count()
    enquete_map = {}
    for call in success_calls.select_related("company"):
        product = call.company.product or "Non renseigné"
        status = call.enquete_status()
        bucket = enquete_map.setdefault(product, {"Complet": 0, "Partiel": 0, "Incomplet": 0})
        bucket[status] = bucket.get(status, 0) + 1
    enquete_by_product = [
        {"product": prod, **stats} for prod, stats in sorted(enquete_map.items(), key=lambda x: x[0].lower())
    ]

    context = {
        "total_companies": total_companies,
        "pending": status_map.get("pending", 0),
        "in_progress": status_map.get("in_progress", 0),
        "done": status_map.get("done", 0),
        "calls_total": success_calls.count(),
        "calls_answered": answered,
        "calls_by_status": calls_by_status,
        "product_counts": product_counts,
        "calls_with_audio": calls_with_audio,
        "calls_without_audio": calls_without_audio,
        "enquete_by_product": enquete_by_product,
    }
    return render(request, "home/dashboard.html", context)


def contacts(request: HttpRequest) -> HttpResponse:
    _ensure_seed_data()
    companies = Company.objects.all().order_by("name")
    return render(request, "home/contacts.html", {"companies": companies})


def call_access(request: HttpRequest) -> HttpResponse:
    password_value = ""
    if request.method == "POST":
        password_value = request.POST.get("password", "")
        user_model = get_user_model()
        found_user = None
        for candidate in user_model.objects.filter(is_active=True):
            authed = authenticate(request, username=candidate.get_username(), password=password_value)
            if authed is not None:
                found_user = authed
                break

        if found_user:
            login(request, found_user)
            request.session["welcome_user"] = found_user.get_username()
            messages.success(request, "Connexion réussie.")
            return redirect("call_list")
        messages.error(request, "Mot de passe invalide.")

    return render(request, "home/call_access.html", {"password_value": password_value})


def call_list(request: HttpRequest) -> HttpResponse:
    if not _require_access(request):
        return redirect("call_access")
    _ensure_seed_data()
    companies = list(Company.objects.all().order_by("status", "name"))
    latest_call = {}
    for call in (
        CallRecord.objects.select_related("company", "user")
        .prefetch_related("recordings")
        .order_by("-created_at")
    ):
        if call.company_id in latest_call:
            continue
        latest_call[call.company_id] = call

    call_rows = []
    for c in companies:
        call = latest_call.get(c.id)
        rec = call.recordings.order_by("-created_at").first() if call else None
        inspector = call.user.get_username() if call and call.user else None
        enquete = call.enquete_status() if call else ""
        call_rows.append({"company": c, "recording": rec, "inspector": inspector, "enquete": enquete})
    welcome_user = request.session.pop("welcome_user", None)
    paginator = Paginator(call_rows, 50)
    page_number = request.GET.get("page") or 1
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "home/call_list.html",
        {"page_obj": page_obj, "welcome_user": welcome_user},
    )


def company_statuses(request: HttpRequest) -> JsonResponse:
    """AJAX: retourne les statuts/inspecteurs par entreprise."""
    companies = list(Company.objects.all().order_by("id"))
    latest_call = {}
    for call in (
        CallRecord.objects.select_related("company", "user")
        .order_by("-created_at")
    ):
        if call.company_id in latest_call:
            continue
        latest_call[call.company_id] = call

    payload = []
    for c in companies:
        call = latest_call.get(c.id)
        inspector = call.user.get_username() if call and call.user else None
        payload.append(
            {
                "id": c.id,
                "status": c.status,
                "status_display": c.get_status_display(),
                "inspector": inspector,
            }
        )
    return JsonResponse({"companies": payload})


def user_stats(request: HttpRequest) -> JsonResponse:
    """AJAX: stats utilisateurs (points, complet/incomplet)."""
    return JsonResponse({"users": _user_cards()})


def export_calls(request: HttpRequest) -> HttpResponse:
    """Affiche/exporte tous les appels."""
    records = (
        CallRecord.objects.select_related("company", "user")
        .prefetch_related("recordings")
        .order_by("-created_at")
    )

    rows = []
    for call in records:
        c = call.company
        has_audio = call.recordings.exists()
        enquete = call.enquete_status()
        rows.append(
            [
                c.name,
                c.phone,
                c.product,
                c.activity,
                c.location,
                c.legal_form,
                c.niu,
                c.validity_score,
                call.get_status_numero_display(),
                call.get_call_status_display() if call.call_status else "",
                call.get_presentation_level_display() if call.presentation_level else "",
                call.get_questions_libres_level_display() if call.questions_libres_level else "",
                call.get_questions_orientees_level_display() if call.questions_orientees_level else "",
                enquete,
                (call.status_marked_at or call.created_at).strftime("%Y-%m-%d %H:%M"),
                "Oui" if has_audio else "Non",
            ]
        )

    if request.method == "POST" and request.POST.get("action") == "export":
        fmt = request.POST.get("format", "csv")
        today = timezone.now().strftime("%Y%m%d")
        filename = f"PME_Transformation_consolidee_{today}"
        header = [
            "Nom de l'entreprise", "Téléphone", "Produit", "Activité", "Localisation",
            "Régime/Forme", "NIU", "Validité score", "Statut numéros", "Statut appel",
            "Présentation", "Questions libres", "Questions orientées", "Enquête",
            "Date-temps", "Enregistrement vocal",
        ]
        if fmt == "excel":
            import csv
            import io

            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer, delimiter="\t")
            writer.writerow(header)
            writer.writerows(rows)
            data = buffer.getvalue().encode("utf-8")
            resp = HttpResponse(data, content_type="application/vnd.ms-excel")
            resp["Content-Disposition"] = f'attachment; filename="{filename}.xlsm"'
            return resp
        else:
            import csv
            import io

            buffer = io.StringIO(newline="")
            writer = csv.writer(buffer)
            writer.writerow(header)
            writer.writerows(rows)
            data = buffer.getvalue().encode("utf-8")
            resp = HttpResponse(data, content_type="text/csv; charset=utf-8")
            resp["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
            return resp

    return render(request, "home/export.html", {"rows": rows})


def call_form(request: HttpRequest, company_id: int) -> HttpResponse:
    if not _require_access(request):
        return redirect("call_access")

    company = get_object_or_404(Company, id=company_id)
    if company.status == "done":
        messages.info(request, "Cette entreprise est déjà marquée comme appelée.")
        return redirect("call_list")

    if company.status != "in_progress":
        company.status = "in_progress"
        company.save(update_fields=["status"])

    initial = {}
    if request.method == "POST":
        form = CallRecordForm(request.POST)
        if form.is_valid():
            record: CallRecord = form.save(commit=False)
            record.company = company
            if request.user.is_authenticated:
                record.user = request.user
            call_status = form.cleaned_data.get("call_status")
            if call_status == "callback":
                company.status = "callback"
            else:
                company.status = "done"
            company.save(update_fields=["status"])
            ts_val = form.cleaned_data.get("status_marked_at")
            if ts_val:
                try:
                    if isinstance(ts_val, str):
                        record.status_marked_at = timezone.datetime.fromisoformat(ts_val)
                    else:
                        record.status_marked_at = ts_val
                except Exception:
                    record.status_marked_at = timezone.now()
            else:
                record.status_marked_at = timezone.now()
            record.recording_started_at = timezone.now()
            record.recording_stopped_at = timezone.now()
            record.save()
            recording_data = form.cleaned_data.get("recording_data")
            if recording_data:
                try:
                    header, data = recording_data.split(",", 1)
                    mime = form.cleaned_data.get("recording_mime") or header.split(";")[0].replace("data:", "")
                    ext = "webm"
                    if "mp4" in mime:
                        ext = "mp4"
                    company_slug = slugify(company.name) or "entreprise"
                    date_str = timezone.now().strftime("%Y%m%d")
                    audio_bytes = ContentFile(base64.b64decode(data), name=f"{company_slug}_{date_str}.{ext}")
                    from .models import Recording

                    Recording.objects.create(call=record, file=audio_bytes, mime_type=mime, duration_seconds=0)
                except Exception:
                    messages.warning(request, "Impossible d'enregistrer le fichier audio.")
            messages.success(request, "Enregistrement sauvegarde.")
            return redirect(reverse("call_list"))
    else:
        form = CallRecordForm(initial=initial)

    return render(
        request,
        "home/call_form.html",
        {
            "company": company,
            "form": form,
        },
    )


def import_companies(request: HttpRequest) -> HttpResponse:
    form = ImportCompaniesForm()
    imported = 0
    preview_rows = []
    payload_json = ""
    session_key = "import_preview_rows"

    def parse_csv(uploaded_file):
        raw_bytes = uploaded_file.read()
        try:
            data = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                data = raw_bytes.decode("latin-1")
            except UnicodeDecodeError:
                raise ValueError("Impossible de lire le fichier CSV.")

        sample_lines = [line for line in data.splitlines() if line.strip()][:5]
        delimiter = ","
        if sample_lines:
            comma_score = sum(line.count(",") for line in sample_lines)
            semicolon_score = sum(line.count(";") for line in sample_lines)
            delimiter = ";" if semicolon_score > comma_score else ","

        try:
            has_header = csv.Sniffer().has_header("\n".join(sample_lines)) if sample_lines else True
        except Exception:
            has_header = True

        def pick(row_obj, keys, fallback_index=None):
            if isinstance(row_obj, dict):
                for k in keys:
                    if k in row_obj and row_obj[k] not in (None, ""):
                        return row_obj[k]
            else:
                if fallback_index is not None and fallback_index < len(row_obj):
                    return row_obj[fallback_index]
            return ""

        def trim(val, limit=255):
            return str(val)[:limit] if val is not None else ""

        rows_iter = (
            csv.DictReader(StringIO(data), delimiter=delimiter)
            if has_header
            else csv.reader(StringIO(data), delimiter=delimiter)
        )

        parsed = []
        for idx, row in enumerate(rows_iter, start=1):
            name_val = pick(row, ["name", "Name", "nom", "Nom"], fallback_index=0)
            phone_val = pick(row, ["phone", "Phone", "tel", "Tel","Telephone","Téléphone"], fallback_index=1)
            product_val = pick(row, ["product", "Product", "filiere","Produit","produit","filières"], fallback_index=2)
            activity_val = pick(row, ["activity", "Activity","Activité"], fallback_index=3)
            location_val = pick(row, ["location", "Location","Localisation"], fallback_index=4)
            legal_form_val = pick(row, ["legal_form", "Legal_form", "forme"], fallback_index=5)
            niu_val = pick(row, ["niu", "NIU"], fallback_index=6)
            validity_val = pick(row, ["validity_score", "score"], fallback_index=7)
            status_val = pick(row, ["status", "etat"], fallback_index=8)

            name = trim(name_val) or f"Entreprise {idx}"
            phone = trim(phone_val) or "Non renseigne"
            try:
                validity_score = float(validity_val) if validity_val not in ("", None) else 0
            except ValueError:
                validity_score = 0
            status = trim(status_val) or "pending"
            if status not in dict(Company.STATUS_CHOICES):
                status = "pending"

            parsed.append(
                {
                    "name": trim(name),
                    "phone": trim(phone),
                    "product": trim(product_val),
                    "activity": trim(activity_val),
                    "location": trim(location_val),
                    "legal_form": trim(legal_form_val),
                    "niu": trim(niu_val),
                    "validity_score": validity_score,
                    "status": status,
                }
            )
        return parsed

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirm":
            payload_json = request.POST.get("payload", "[]")
            try:
                rows = json.loads(payload_json)
            except json.JSONDecodeError:
                rows = request.session.get(session_key, [])
            if not rows:
                messages.error(request, "Aucune donnee a enregistrer.")
                return redirect("import_companies")
            with transaction.atomic():
                Company.objects.all().delete()
                to_create = [Company(**row) for row in rows]
                Company.objects.bulk_create(to_create)
            request.session.pop(session_key, None)
            imported = len(rows)
            messages.success(request, f"{imported} entreprises enregistrees (ancienne base remplacee).")
            return redirect("contacts")
        else:
            form = ImportCompaniesForm(request.POST, request.FILES)
            if form.is_valid():
                upload = form.cleaned_data["file"]
                try:
                    preview_rows = parse_csv(upload)
                    payload_json = json.dumps(preview_rows)
                    request.session[session_key] = preview_rows
                    if not preview_rows:
                        messages.info(request, "Aucune ligne trouvee dans le CSV.")
                except ValueError as exc:
                    messages.error(request, str(exc))
            else:
                messages.error(request, "Fichier invalide.")

    return render(
        request,
        "home/import_companies.html",
        {"form": form, "imported": imported, "preview_rows": preview_rows, "payload_json": payload_json},
    )


@require_POST
def reset_company_status(request: HttpRequest, company_id: int) -> JsonResponse:
    """Réinitialise un statut en cours vers pending si aucun enregistrement n'a été validé."""
    company = get_object_or_404(Company, id=company_id)
    if company.status == "in_progress":
        company.status = "pending"
        company.save(update_fields=["status"])
    return JsonResponse({"status": company.status})
