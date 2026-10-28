from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PatientProfile, TherapistProfile, User
from common.test_utils import auth_client, create_patient, create_therapist


class RegistrationTests(APITestCase):
    def test_patient_registration_creates_patient_profile(self):
        url = reverse("auth-register")
        response = self.client.post(url, {
            "email": "newpatient@example.com",
            "password": "StrongPass123!",
            "first_name": "Pat",
            "last_name": "Ient",
            "role": "patient",
            "timezone": "America/New_York",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(email="newpatient@example.com")
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(PatientProfile.objects.filter(user=user, timezone="America/New_York").exists())

    def test_therapist_registration_creates_therapist_profile(self):
        url = reverse("auth-register")
        response = self.client.post(url, {
            "email": "newtherapist@example.com",
            "password": "StrongPass123!",
            "role": "therapist",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        user = User.objects.get(email="newtherapist@example.com")
        self.assertEqual(user.role, User.Role.THERAPIST)
        self.assertTrue(TherapistProfile.objects.filter(user=user).exists())

    def test_invalid_timezone_rejected(self):
        url = reverse("auth-register")
        response = self.client.post(url, {
            "email": "bad@example.com",
            "password": "StrongPass123!",
            "role": "patient",
            "timezone": "Not/AZone",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginAndMeTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="p1@example.com", password="StrongPass123!")

    def test_login_returns_tokens_with_role_claim(self):
        url = reverse("auth-login")
        response = self.client.post(url, {"email": "p1@example.com", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_endpoint_includes_profile(self):
        client = auth_client(self.patient)
        response = client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], "patient")
        self.assertIsNotNone(response.data["profile"])

    def test_logout_blacklists_refresh_token(self):
        login_response = self.client.post(reverse("auth-login"), {"email": "p1@example.com", "password": "StrongPass123!"})
        refresh = login_response.data["refresh"]
        client = auth_client(self.patient)
        logout_response = client.post(reverse("auth-logout"), {"refresh": refresh})
        self.assertEqual(logout_response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_response = self.client.post(reverse("auth-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class TherapistDirectoryTests(APITestCase):
    def test_directory_excludes_patient_data_and_license_number(self):
        therapist = create_therapist(email="dirtherapist@example.com")
        therapist.therapist_profile.license_number = "SECRET-LICENSE-1"
        therapist.therapist_profile.bio = "Specialises in CBT."
        therapist.therapist_profile.save()
        patient = create_patient(email="dirpatient@example.com")

        client = auth_client(patient)
        response = client.get(reverse("therapist-directory"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(r for r in response.data["results"] if r["email"] == "dirtherapist@example.com")
        self.assertNotIn("license_number", row)
