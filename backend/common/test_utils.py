from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PatientProfile, TherapistProfile, User


def create_patient(email="patient@example.com", password="StrongPass123!", timezone="UTC", **kwargs):
    user = User.objects.create_user(email=email, password=password, role=User.Role.PATIENT, **kwargs)
    PatientProfile.objects.create(user=user, timezone=timezone)
    return user


def create_therapist(email="therapist@example.com", password="StrongPass123!", **kwargs):
    user = User.objects.create_user(email=email, password=password, role=User.Role.THERAPIST, **kwargs)
    TherapistProfile.objects.create(user=user)
    return user


def auth_client(user) -> APIClient:
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client
