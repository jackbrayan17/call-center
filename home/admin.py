from django.contrib import admin
from django.http import HttpResponse
import csv

from .models import AuditLog, CallRecord, Company, Recording, SessionSnapshot


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "product", "status")
    search_fields = ("name", "phone", "product", "activity")


@admin.register(CallRecord)
class CallRecordAdmin(admin.ModelAdmin):
    list_display = ("company", "status_numero", "call_status", "user", "created_at")
    search_fields = ("company__name", "user__username")
    list_filter = ("status_numero", "call_status")


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("call", "mime_type", "created_at")
    search_fields = ("call__company__name",)


@admin.register(SessionSnapshot)
class SessionSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "ip_address", "is_active", "login_at", "last_activity")
    search_fields = ("user__username", "session_key", "ip_address")
    list_filter = ("is_active",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "method", "path", "status_code", "ip_address", "duration_ms")
    search_fields = ("path", "user__username", "ip_address", "session_key")
    list_filter = ("method", "status_code")
    actions = ["export_csv"]

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(["created_at", "user", "method", "path", "status", "ip", "session", "duration_ms", "payload"])
        for log in queryset:
            writer.writerow([
                log.created_at.isoformat(),
                log.user.get_username() if log.user else "",
                log.method,
                log.path,
                log.status_code,
                log.ip_address,
                log.session_key,
                log.duration_ms,
                log.payload_summary,
            ])
        return response

    export_csv.short_description = "Exporter en CSV"
