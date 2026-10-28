"""
Data-isolation building blocks for MindTrack.

Per spec, therapist access to any patient data must be scoped at the
QUERYSET level - never a serializer-only hide - so that a therapist cannot
retrieve another therapist's patient's data even by guessing an object ID.
Every view that exposes patient-owned data (journals, therapy notes,
analytics, alerts) filters its queryset through
`active_patient_ids_for_therapist` rather than relying solely on
`has_object_permission`.
"""
from rest_framework.permissions import BasePermission

from apps.therapy_links.models import PatientTherapistLink


def active_patient_ids_for_therapist(therapist):
    """Queryset (not a list) of patient user IDs the therapist currently has
    an ACTIVE link to. Used to scope every patient-data queryset a
    therapist can touch."""
    return PatientTherapistLink.objects.filter(
        therapist=therapist, status=PatientTherapistLink.Status.ACTIVE
    ).values_list("patient_id", flat=True)


def is_linked(therapist, patient) -> bool:
    if therapist is None or patient is None:
        return False
    return PatientTherapistLink.objects.filter(
        therapist=therapist, patient=patient, status=PatientTherapistLink.Status.ACTIVE
    ).exists()


class IsPatientOwner(BasePermission):
    """Grants access only when the requesting user IS the patient who owns
    the object (object must expose `.patient` or `.patient_id`)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "is_patient", False))

    def has_object_permission(self, request, view, obj):
        patient_id = getattr(obj, "patient_id", None)
        if patient_id is None:
            patient = getattr(obj, "patient", None)
            patient_id = getattr(patient, "id", None)
        return bool(
            request.user.is_authenticated
            and getattr(request.user, "is_patient", False)
            and patient_id == request.user.id
        )


class IsLinkedTherapist(BasePermission):
    """Grants access only when the requesting user is a therapist with an
    ACTIVE PatientTherapistLink to the object's patient.

    This is a defense-in-depth object-level check; the primary isolation
    boundary is always the queryset scoping (`active_patient_ids_for_therapist`)
    applied in each view's `get_queryset`.
    """

    is_linked = staticmethod(is_linked)

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "is_therapist", False))

    def has_object_permission(self, request, view, obj):
        patient = getattr(obj, "patient", None) or obj
        return is_linked(request.user, patient)


class IsPatientOwnerOrLinkedTherapist(BasePermission):
    """Read access for the owning patient OR a therapist with an active
    link; write access limited to the owning patient (used by views like
    JournalEntry where only the patient may create/edit their own entries)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        patient_id = getattr(obj, "patient_id", None)
        if patient_id is None:
            patient = getattr(obj, "patient", None)
            patient_id = getattr(patient, "id", None)

        if getattr(user, "is_patient", False) and patient_id == user.id:
            return True

        if getattr(user, "is_therapist", False) and request.method in ("GET", "HEAD", "OPTIONS"):
            patient = getattr(obj, "patient", None)
            return is_linked(user, patient) if patient is not None else False

        return False
