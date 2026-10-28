from django.conf import settings
from django.db import models

from apps.therapy_links.models import PatientTherapistLink


class SessionNote(models.Model):
    """Therapist-authored note about a session with a patient.

    `visible_to_patient` gates whether the patient-facing endpoints ever
    return this row - patient-facing querysets filter on
    `visible_to_patient=True` unconditionally (see views.py), this is never
    left to the frontend to hide.

    Per spec: "ended links hide live dashboard access but preserve
    historical session-note visibility" - i.e. once a link ends, the
    therapist can no longer pull the patient's live journal/trend data, but
    notes already marked visible_to_patient stay visible to the patient, and
    the therapist can still see notes they personally authored (read-only
    historical record), even after the link ends.
    """

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="session_notes"
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authored_session_notes"
    )
    link = models.ForeignKey(
        PatientTherapistLink, on_delete=models.SET_NULL, null=True, blank=True, related_name="session_notes"
    )
    session_date = models.DateField()
    note_text = models.TextField()
    # Hardening note (see README / journals/models.py): recommend field-level
    # encryption of note_text in a real deployment.
    visible_to_patient = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-session_date", "-created_at"]
        indexes = [
            models.Index(fields=["patient", "visible_to_patient"]),
            models.Index(fields=["therapist"]),
        ]

    def __str__(self):
        return f"SessionNote(patient={self.patient_id}, therapist={self.therapist_id}, {self.session_date})"
