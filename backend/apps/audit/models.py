from django.conf import settings
from django.db import models


class AccessLog(models.Model):
    """Audit trail row written every time a therapist views a patient's
    journal entries, mood trend, or symptom-frequency data (spec: 'every
    therapist view of patient journal/trend data gets logged').

    Written via explicit `log_access()` calls at the top of the relevant
    views rather than generic middleware, because only a few, well-known
    read endpoints need logging and an explicit call at the call site is
    easier to verify in tests and to reason about than pattern-matching
    arbitrary URLs in middleware.
    """

    class Action(models.TextChoices):
        JOURNAL_VIEW = "journal_view", "Journal entries viewed"
        TREND_VIEW = "trend_view", "Mood trend viewed"
        SYMPTOM_FREQUENCY_VIEW = "symptom_frequency_view", "Symptom frequency viewed"
        DASHBOARD_VIEW = "dashboard_view", "Dashboard summary viewed"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_logs_made"
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="access_logs_about"
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["patient", "timestamp"]),
            models.Index(fields=["actor", "timestamp"]),
        ]

    def __str__(self):
        return f"AccessLog({self.actor_id} -> {self.patient_id}, {self.action})"


def log_access(actor, patient, action: str, **metadata):
    """Convenience helper used from views: `log_access(request.user, patient, AccessLog.Action.JOURNAL_VIEW)`.

    `patient` may be a User instance or a raw user id (e.g. straight from a
    query parameter) - both are accepted so call sites don't need to fetch
    the full object just to log against it.
    """
    patient_id = getattr(patient, "id", patient)
    return AccessLog.objects.create(actor=actor, patient_id=patient_id, action=action, metadata=metadata)
