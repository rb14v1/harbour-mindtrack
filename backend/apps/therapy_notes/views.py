from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.therapy_notes.models import SessionNote
from apps.therapy_notes.serializers import PatientSessionNoteSerializer, SessionNoteSerializer


class SessionNoteViewSet(viewsets.ModelViewSet):
    """
    - Therapist: sees/edits notes THEY authored (this naturally preserves
      historical visibility after a link ends - spec: "ended links hide
      live dashboard access but preserve historical session-note
      visibility" - since the scoping key is authorship, not current link
      status). Creating a NEW note still requires an ACTIVE link, enforced
      in the serializer.
    - Patient: read-only, and the queryset is unconditionally filtered to
      `visible_to_patient=True` - a therapist's private/draft notes about a
      patient are never retrievable via the patient-facing endpoint,
      regardless of serializer field selection.
    """

    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.is_patient:
            return PatientSessionNoteSerializer
        return SessionNoteSerializer

    def get_queryset(self):
        user = self.request.user
        qs = SessionNote.objects.select_related("patient", "therapist")

        if user.is_patient:
            return qs.filter(patient=user, visible_to_patient=True).order_by("-session_date")

        if user.is_therapist:
            return qs.filter(therapist=user).order_by("-session_date")

        return qs.none()

    def perform_create(self, serializer):
        if not self.request.user.is_therapist:
            raise PermissionDenied("Only therapists can author session notes.")
        serializer.save()
