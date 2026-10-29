import secrets

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PatientProfile, TherapistProfile, User


def _random_password() -> str:
    """Generate a throwaway password for test fixtures (never hardcode one)."""
    return secrets.token_urlsafe(24)


def create_patient(email="patient@example.com", password=None, timezone="UTC", **kwargs):
    user = User.objects.create_user(
        email=email, password=password or _random_password(), role=User.Role.PATIENT, **kwargs
    )
    PatientProfile.objects.create(user=user, timezone=timezone)
    return user


def create_therapist(email="therapist@example.com", password=None, **kwargs):
    user = User.objects.create_user(
        email=email, password=password or _random_password(), role=User.Role.THERAPIST, **kwargs
    )
    TherapistProfile.objects.create(user=user)
    return user


def auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client
