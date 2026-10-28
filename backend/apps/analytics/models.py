from django.conf import settings
from django.db import models
from django.db.models import Q


class Alert(models.Model):
    """System- or therapist-triggered flag on a patient.

    Every rule_type is an explicit, documented condition (see
    services/trend_detection.py and journals/services/alerts.py) - there is
    no ML/black-box scoring anywhere in this app, by design (spec
    requirement), so every alert can be explained to a clinician in one
    sentence.

    Idempotency: at most one OPEN alert of a given rule_type may exist per
    patient at a time (enforced both by the partial unique constraint below
    and, for belt-and-braces clarity in the service layer, an explicit
    existence check before create).
    """

    class RuleType(models.TextChoices):
        LOW_MOOD_ENTRY = "low_mood_entry", "Single very-low mood entry"
        LOW_MEAN_MOOD_7D = "low_mean_mood_7d", "Low mean mood over trailing window"
        CONSECUTIVE_LOW_MOOD = "consecutive_low_mood", "Consecutive low-mood entries"
        NO_ENTRY_STREAK = "no_entry_streak", "No journal entries for several days"
        THERAPIST_FLAGGED = "therapist_flagged", "Manually flagged by therapist"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    class TriggeredBy(models.TextChoices):
        SYSTEM = "system", "System"
        THERAPIST = "therapist", "Therapist"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts"
    )
    rule_type = models.CharField(max_length=32, choices=RuleType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    triggered_by = models.CharField(max_length=16, choices=TriggeredBy.choices, default=TriggeredBy.SYSTEM)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts_created",
        help_text="Set only for therapist-triggered alerts.",
    )
    source_entry = models.ForeignKey(
        "journals.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_alerts",
        help_text="Set for the low_mood_entry fast-path rule.",
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts_acknowledged"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts_resolved"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "rule_type"],
                condition=Q(status="open"),
                name="unique_open_alert_per_patient_rule",
            ),
        ]
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient", "status"])]

    def __str__(self):
        return f"Alert({self.patient_id}, {self.rule_type}, {self.status})"
