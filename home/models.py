from django.db import models


class Company(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pas encore appelé"),
        ("in_progress", "En cours"),
        ("callback", "Rappel"),
        ("done", "Déjà appelé"),
    ]

    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    product = models.CharField(max_length=255, blank=True)
    activity = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    legal_form = models.CharField(max_length=255, blank=True)
    niu = models.CharField(max_length=128, blank=True)
    validity_score = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")

    def __str__(self) -> str:
        return self.name


class CallRecord(models.Model):
    STATUS_NUMERO_CHOICES = [
        ("invalid", "Invalide"),
        ("no_answer", "Ne décroche pas"),
        ("voicemail", "Répondeur"),
        ("answered", "Décroche l'appel"),
    ]
    CALL_STATUS_CHOICES = [
        ("bad_number", "Mauvais numéro"),
        ("not_transformer", "Pas transformateur"),
        ("callback", "Rappel"),
        ("refused", "Refuse le questionnaire"),
        ("accepted", "Accepte le questionnaire"),
    ]
    LEVEL_CHOICES = [
        ("", "Vide"),
        ("partial", "Partiel"),
        ("complete", "Complet"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="calls")
    status_numero = models.CharField(max_length=32, choices=STATUS_NUMERO_CHOICES)
    call_status = models.CharField(max_length=32, choices=CALL_STATUS_CHOICES, blank=True)
    presentation_level = models.CharField(max_length=16, choices=LEVEL_CHOICES, blank=True)
    questions_libres_level = models.CharField(max_length=16, choices=LEVEL_CHOICES, blank=True)
    questions_orientees_level = models.CharField(max_length=16, choices=LEVEL_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status_marked_at = models.DateTimeField(null=True, blank=True)
    recording_started_at = models.DateTimeField(null=True, blank=True)
    recording_stopped_at = models.DateTimeField(null=True, blank=True)
    recording_path = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="call_records")

    def __str__(self) -> str:
        return f"Call {self.company.name} - {self.get_status_numero_display()}"

    def enquete_status(self) -> str:
        """Compute survey status based on questionnaire levels."""
        if self.call_status != "accepted":
            return "Incomplet"
        levels = [
            self.presentation_level,
            self.questions_libres_level,
            self.questions_orientees_level,
        ]
        if all(level == "complete" for level in levels):
            return "Complet"
        if any(level == "partial" for level in levels):
            return "Partiel"
        return "Partiel"


class Recording(models.Model):
    call = models.ForeignKey(CallRecord, on_delete=models.CASCADE, related_name="recordings")
    file = models.FileField(upload_to="recordings/")
    mime_type = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"Recording for {self.call}"
