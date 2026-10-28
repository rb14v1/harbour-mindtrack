from datetime import timedelta

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.analytics.models import Alert
from apps.analytics.serializers import AlertSerializer, CreateManualAlertSerializer
from apps.audit.models import AccessLog, log_access
from apps.journals.models import JournalEntry, JournalEntrySymptom
from apps.therapy_links.models import PatientTherapistLink
from apps.therapy_links.permissions import active_patient_ids_for_therapist, is_linked


def _resolve_patient_for_viewer(request, patient_id) -> User:
    """Shared access check for the per-patient analytics endpoints: the
    patient themself, or a therapist with an ACTIVE link to them. Returns
    the User row or raises NotFound/PermissionDenied - deliberately
    NotFound (404) rather than 403 for an unlinked therapist, so that ID
    guessing can't even distinguish "exists but not yours" from "doesn't
    exist"."""
    patient = get_object_or_404(User, id=patient_id, role=User.Role.PATIENT)

    user = request.user
    if user.is_patient:
        if user.id != patient.id:
            raise NotFound("Not found.")
        return patient

    if user.is_therapist:
        if not is_linked(user, patient):
            raise NotFound("Not found.")
        return patient

    raise PermissionDenied("Unrecognised role.")


class PatientMoodTrendView(APIView):
    """GET /api/analytics/patients/<id>/trend/?days=30

    Returns the patient's mood/energy/sleep time series for the trailing
    `days` days (default 30). A therapist request writes an AccessLog row;
    a patient viewing their own data does not (no audit need for
    self-access)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        patient = _resolve_patient_for_viewer(request, patient_id)

        days = int(request.query_params.get("days", 30))
        days = max(1, min(days, 365))
        since = timezone.now().date() - timedelta(days=days - 1)

        entries = (
            JournalEntry.objects.filter(patient=patient, entry_date__gte=since)
            .select_related("mood_score")
            .order_by("entry_date")
        )
        points = [
            {
                "entry_date": e.entry_date,
                "score": e.mood_score.score if hasattr(e, "mood_score") else None,
                "energy_level": e.mood_score.energy_level if hasattr(e, "mood_score") else None,
                "sleep_hours": float(e.mood_score.sleep_hours) if hasattr(e, "mood_score") and e.mood_score.sleep_hours is not None else None,
            }
            for e in entries
        ]

        if request.user.is_therapist:
            log_access(request.user, patient, AccessLog.Action.TREND_VIEW, days=days)

        scored = [p["score"] for p in points if p["score"] is not None]
        mean_score = round(sum(scored) / len(scored), 2) if scored else None

        return Response({
            "patient": patient.id,
            "window_days": days,
            "mean_score": mean_score,
            "points": points,
        })


class PatientSymptomFrequencyView(APIView):
    """GET /api/analytics/patients/<id>/symptom-frequency/?days=30"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        patient = _resolve_patient_for_viewer(request, patient_id)

        days = int(request.query_params.get("days", 30))
        days = max(1, min(days, 365))
        since = timezone.now().date() - timedelta(days=days - 1)

        rows = (
            JournalEntrySymptom.objects.filter(entry__patient=patient, entry__entry_date__gte=since)
            .values("symptom__name")
            .annotate(count=Count("id"), average_severity=Avg("severity"))
            .order_by("-count")
        )
        data = [
            {
                "symptom": row["symptom__name"],
                "count": row["count"],
                "average_severity": round(row["average_severity"], 2) if row["average_severity"] is not None else None,
            }
            for row in rows
        ]

        if request.user.is_therapist:
            log_access(request.user, patient, AccessLog.Action.SYMPTOM_FREQUENCY_VIEW, days=days)

        return Response({"patient": patient.id, "window_days": days, "symptoms": data})


class TherapistDashboardView(APIView):
    """GET /api/analytics/dashboard/

    Therapist-only roster summary: every ACTIVELY linked patient, their
    latest mood score, days since last entry, and count of open alerts.
    Scoped structurally via active_patient_ids_for_therapist - a therapist
    can never see a summary row for a patient they aren't actively linked
    to."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_therapist:
            raise PermissionDenied("Dashboard is therapist-only.")

        patient_ids = list(active_patient_ids_for_therapist(request.user))
        rows = []
        for patient in User.objects.filter(id__in=patient_ids):
            latest_entry = (
                JournalEntry.objects.filter(patient=patient).select_related("mood_score").order_by("-entry_date").first()
            )
            open_alert_count = Alert.objects.filter(patient=patient, status=Alert.Status.OPEN).count()
            rows.append({
                "patient": patient.id,
                "patient_name": f"{patient.first_name} {patient.last_name}".strip() or patient.email,
                "patient_email": patient.email,
                "latest_entry_date": latest_entry.entry_date if latest_entry else None,
                "latest_mood_score": (
                    latest_entry.mood_score.score if latest_entry and hasattr(latest_entry, "mood_score") else None
                ),
                "open_alert_count": open_alert_count,
            })
            log_access(request.user, patient, AccessLog.Action.DASHBOARD_VIEW)

        return Response({"patients": rows})


class AlertViewSet(viewsets.ModelViewSet):
    """
    - Patient: sees only their own alerts (list/retrieve); cannot create,
      acknowledge or resolve (alerts are reviewed by a clinician).
    - Therapist: sees alerts for ACTIVELY-linked patients only (structural
      queryset scoping, same pattern as journals); can acknowledge/resolve;
      can manually create a THERAPIST_FLAGGED alert via POST.
    """

    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["status", "rule_type", "patient"]

    def get_queryset(self):
        user = self.request.user
        qs = Alert.objects.select_related("patient")
        if user.is_patient:
            return qs.filter(patient=user)
        if user.is_therapist:
            return qs.filter(patient_id__in=active_patient_ids_for_therapist(user))
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not request.user.is_therapist:
            raise PermissionDenied("Only therapists can manually flag an alert.")
        serializer = CreateManualAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = get_object_or_404(User, id=serializer.validated_data["patient"], role=User.Role.PATIENT)
        if not is_linked(request.user, patient):
            raise NotFound("Not found.")

        alert = Alert.objects.create(
            patient=patient,
            rule_type=Alert.RuleType.THERAPIST_FLAGGED,
            triggered_by=Alert.TriggeredBy.THERAPIST,
            created_by=request.user,
            message=serializer.validated_data["message"],
        )
        return Response(AlertSerializer(alert).data, status=status.HTTP_201_CREATED)

    def _transition(self, request, pk, *, to_status, timestamp_field, by_field):
        alert = self.get_object()
        if not request.user.is_therapist:
            raise PermissionDenied("Only a therapist can update alert status.")
        if alert.status == Alert.Status.RESOLVED:
            raise ValidationError("Alert is already resolved.")

        setattr(alert, timestamp_field, timezone.now())
        setattr(alert, by_field, request.user)
        alert.status = to_status
        alert.save()
        return Response(AlertSerializer(alert).data)

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        return self._transition(
            request, pk, to_status=Alert.Status.ACKNOWLEDGED,
            timestamp_field="acknowledged_at", by_field="acknowledged_by",
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        return self._transition(
            request, pk, to_status=Alert.Status.RESOLVED,
            timestamp_field="resolved_at", by_field="resolved_by",
        )
