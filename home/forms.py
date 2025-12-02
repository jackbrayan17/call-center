from django import forms

from .models import CallRecord


class CallRecordForm(forms.ModelForm):
    recording_data = forms.CharField(required=False, widget=forms.HiddenInput())
    recording_started = forms.BooleanField(required=False, widget=forms.HiddenInput())
    skip_without_rec = forms.BooleanField(required=False, widget=forms.HiddenInput())
    recording_mime = forms.CharField(required=False, widget=forms.HiddenInput())
    questionnaire_data = forms.JSONField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = CallRecord
        fields = [
            "status_numero",
            "call_status",
            "presentation_level",
            "questions_libres_level",
            "questions_orientees_level",
            "status_marked_at",
            "recording_data",
            "recording_started",
            "skip_without_rec",
            "recording_mime",
            "questionnaire_data",
        ]
        widgets = {
            "status_numero": forms.Select(attrs={"class": "input"}),
            "call_status": forms.Select(attrs={"class": "input"}),
            "presentation_level": forms.Select(attrs={"class": "input"}),
            "questions_libres_level": forms.Select(attrs={"class": "input"}),
            "questions_orientees_level": forms.Select(attrs={"class": "input"}),
            "status_marked_at": forms.HiddenInput(),
        }

    def clean(self):
        cleaned = super().clean()
        status_numero = cleaned.get("status_numero")
        call_status = cleaned.get("call_status")

        if status_numero == "answered" and not call_status:
            self.add_error("call_status", "Choisissez un statut d'appel.")
        if call_status != "accepted":
            cleaned["presentation_level"] = ""
            cleaned["questions_libres_level"] = ""
            cleaned["questions_orientees_level"] = ""
        if not cleaned.get("status_marked_at"):
            self.add_error("status_numero", "Cliquez d'abord sur un statut.")
        if not cleaned.get("recording_started") and not cleaned.get("skip_without_rec"):
            self.add_error("status_numero", "Lancez le micro ou continuez sans enregistrement avant de sélectionner un statut.")
        return cleaned


class ImportCompaniesForm(forms.Form):
    file = forms.FileField(
        label="Fichier CSV",
        help_text="Accepte tout CSV (délimiteur auto-détecté, en-têtes optionnelles).",
    )
