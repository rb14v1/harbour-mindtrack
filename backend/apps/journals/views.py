from rest_framework import generics, permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.audit.models import AccessLog, log_access
from apps.journals.models import JournalEntry, SymptomTag
from apps.journals.serializers import JournalEntrySerializer, SymptomTagSerializer
from apps.therapy_links.permissions import IsPatientOwnerOrLinkedTherapist, active_patient_ids_for_therapist


class SymptomTagListView(generics.ListAPIView):
    """Read-only lookup list used to populate the symptom picker in the
    journal entry form."""

    queryset = SymptomTag.objects.filter(is_active=True)
    serializer_class = SymptomTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class JournalEntryViewSet(viewsets.ModelViewSet):
    """
    - Patients: full CRUD on their own entries (one per calendar day, see
      model constraint + serializer validation; edits only within the
      same-day window).
    - Therapists: read-only, and ONLY for patients they have an ACTIVE link
      to - enforced by scoping the queryset itself (never a serializer-only
      hide), per spec. Every list/retrieve by a therapist writes an
      AccessLog row.
    """

    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsPatientOwnerOrLinkedTherapist]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["patient"]

    def get_queryset(self):
        user = self.request.user
        qs = JournalEntry.objects.select_related("mood_score").prefetch_related("symptoms__symptom", "edit_history")

        if user.is_patient:
            return qs.filter(patient=user).order_by("-entry_date")

        if user.is_therapist:
            # Structural scoping: a therapist's queryset can only ever
            # contain rows for patients with a currently-ACTIVE link to
            # them - guessing another therapist's patient's entry ID
            # returns 404, not 403, because the row is excluded here.
            return qs.filter(patient_id__in=active_patient_ids_for_therapist(user)).order_by("-entry_date")

        return qs.none()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.user.is_therapist:
            patient_id = request.query_params.get("patient")
            if patient_id:
                log_access(request.user, patient_id, AccessLog.Action.JOURNAL_VIEW, filtered_patient=patient_id)
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_therapist:
            log_access(request.user, instance.patient_id, AccessLog.Action.JOURNAL_VIEW, entry_id=instance.id)
        return super().retrieve(request, *args, **kwargs)

    def perform_create(self, serializer):
        if not self.request.user.is_patient:
            raise PermissionDenied("Only patients can create journal entries.")
        serializer.save(patient=self.request.user)
