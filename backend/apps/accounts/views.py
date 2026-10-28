from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.models import PatientProfile, TherapistProfile, User
from apps.accounts.serializers import (
    EmailTokenObtainPairSerializer,
    PatientProfileSerializer,
    RegisterSerializer,
    TherapistDirectorySerializer,
    TherapistProfileSerializer,
    UserSerializer,
)
from apps.therapy_links.permissions import IsLinkedTherapist


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class ThrottledTokenRefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutView(APIView):
    """Blacklists the supplied refresh token so it can no longer be used to
    mint new access tokens (requires rest_framework_simplejwt.token_blacklist,
    enabled in INSTALLED_APPS)."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response({"detail": "refresh is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Invalid or already-blacklisted token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        if request.user.is_patient:
            profile = getattr(request.user, "patient_profile", None)
            data["profile"] = PatientProfileSerializer(profile).data if profile else None
        elif request.user.is_therapist:
            profile = getattr(request.user, "therapist_profile", None)
            data["profile"] = TherapistProfileSerializer(profile).data if profile else None
        return Response(data)


class IsOwnerPatientOrLinkedTherapist(permissions.BasePermission):
    """Used on the single-patient-profile endpoint: the patient who owns the
    profile may read/write it; a therapist with an ACTIVE link to that
    patient may read (never write) it."""

    def has_object_permission(self, request, view, obj: PatientProfile):
        user = request.user
        if user.is_patient and obj.user_id == user.id:
            return True
        if user.is_therapist and request.method in permissions.SAFE_METHODS:
            return IsLinkedTherapist().is_linked(therapist=user, patient=obj.user)
        return False


class PatientProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = PatientProfile.objects.select_related("user")
    serializer_class = PatientProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerPatientOrLinkedTherapist]
    lookup_url_kwarg = "user_id"

    def get_object(self):
        profile = get_object_or_404(self.get_queryset(), user_id=self.kwargs["user_id"])
        self.check_object_permissions(self.request, profile)
        return profile


class TherapistProfileDetailView(generics.RetrieveUpdateAPIView):
    queryset = TherapistProfile.objects.select_related("user")
    lookup_url_kwarg = "user_id"

    def get_serializer_class(self):
        if self.request.user.is_authenticated and self.request.user.id == int(self.kwargs["user_id"]):
            return TherapistProfileSerializer
        return TherapistDirectorySerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsSelfTherapist()]

    def get_object(self):
        profile = get_object_or_404(self.get_queryset(), user_id=self.kwargs["user_id"])
        self.check_object_permissions(self.request, profile)
        return profile


class IsSelfTherapist(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: TherapistProfile):
        return request.user.is_therapist and obj.user_id == request.user.id


class TherapistDirectoryListView(generics.ListAPIView):
    """Browsable directory of therapists accepting new patients - used by
    patients to find someone to send a link request to. Never exposes any
    patient data."""

    serializer_class = TherapistDirectorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TherapistProfile.objects.select_related("user").order_by("user__last_name", "user__first_name")
    filterset_fields = ["accepting_new_patients"]
