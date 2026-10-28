from django.conf import settings
from django.db import models
from django.db.models import Q


class PatientTherapistLink(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        ENDED = "ended", "Ended"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="therapy_links_as_patient"
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="therapy_links_as_therapist"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    # Who initiated the request - either party may propose a link.
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="therapy_link_requests_made",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    end_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            # A patient can have at most one ACTIVE link at a time (they may
            # still have other PENDING requests outstanding, and any number
            # of historical ENDED links).
            models.UniqueConstraint(
                fields=["patient"],
                condition=Q(status="active"),
                name="unique_active_link_per_patient",
            ),
            # Don't allow duplicate pending requests between the same pair.
            models.UniqueConstraint(
                fields=["patient", "therapist"],
                condition=Q(status="pending"),
                name="unique_pending_link_per_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["therapist", "status"]),
            models.Index(fields=["patient", "status"]),
        ]

    def __str__(self):
        return f"{self.patient_id} <-> {self.therapist_id} ({self.status})"
