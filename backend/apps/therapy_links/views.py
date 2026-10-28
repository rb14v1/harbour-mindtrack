from django.db import IntegrityError
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.therapy_links.models import PatientTherapistLink
from apps.therapy_links.serializers import (
    CreateLinkSerializer,
    EndLinkSerializer,
    PatientTherapistLinkSerializer,
)


class PatientTherapistLinkViewSet(viewsets.ModelViewSet):
    """
    list/retrieve: a patient sees their own links; a therapist sees links
    where they are the therapist. This is the request/accept/end workflow
    for forming the PatientTherapistLink that everything else (journals
    visibility to therapists, session notes, analytics) depends on.
    """

    serializer_class = PatientTherapistLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = PatientTherapistLink.objects.select_related("patient", "therapist").order_by("-created_at")
        if user.is_patient:
            return qs.filter(patient=user)
        if user.is_therapist:
            return qs.filter(therapist=user)
        return qs.none()

    def create(self, request, *args, **kwargs):
        serializer = CreateLinkSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            link = PatientTherapistLink.objects.create(
                patient=data["patient"],
                therapist=data["therapist"],
                requested_by=request.user,
                status=PatientTherapistLink.Status.PENDING,
            )
        except IntegrityError:
            raise ValidationError(
                "A pending request already exists between this patient and therapist."
            )
        return Response(PatientTherapistLinkSerializer(link).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        link = self.get_object()
        if link.status != PatientTherapistLink.Status.PENDING:
            raise ValidationError("Only a pending link request can be accepted.")
        if link.requested_by_id == request.user.id:
            raise PermissionDenied("The requesting party cannot accept their own request.")
        if link.patient_id != request.user.id and link.therapist_id != request.user.id:
            raise PermissionDenied("Not a party to this link request.")

        try:
            link.status = PatientTherapistLink.Status.ACTIVE
            link.responded_at = timezone.now()
            link.save(update_fields=["status", "responded_at"])
        except IntegrityError:
            raise ValidationError(
                "This patient already has an active therapist link. End it before accepting a new one."
            )
        return Response(PatientTherapistLinkSerializer(link).data)

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        link = self.get_object()
        if link.status not in (PatientTherapistLink.Status.ACTIVE, PatientTherapistLink.Status.PENDING):
            raise ValidationError("Link is already ended.")
        if link.patient_id != request.user.id and link.therapist_id != request.user.id:
            raise PermissionDenied("Not a party to this link.")

        serializer = EndLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        link.status = PatientTherapistLink.Status.ENDED
        link.ended_at = timezone.now()
        link.end_reason = serializer.validated_data.get("reason", "")
        link.save(update_fields=["status", "ended_at", "end_reason"])
        return Response(PatientTherapistLinkSerializer(link).data)
