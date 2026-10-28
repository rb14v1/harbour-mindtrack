from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.therapy_links.models import PatientTherapistLink
from common.test_utils import auth_client, create_patient, create_therapist


class TherapyLinkWorkflowTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="link-patient@example.com")
        self.therapist = create_therapist(email="link-therapist@example.com")

    def test_patient_can_request_and_therapist_can_accept(self):
        patient_client = auth_client(self.patient)
        response = patient_client.post(reverse("therapy-link-list"), {"therapist": self.therapist.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        link_id = response.data["id"]
        self.assertEqual(response.data["status"], "pending")

        therapist_client = auth_client(self.therapist)
        accept_response = therapist_client.post(reverse("therapy-link-accept", args=[link_id]))
        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertEqual(accept_response.data["status"], "active")

    def test_requesting_party_cannot_accept_own_request(self):
        link = PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.PENDING,
        )
        patient_client = auth_client(self.patient)
        response = patient_client.post(reverse("therapy-link-accept", args=[link.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_one_active_link_per_patient(self):
        other_therapist = create_therapist(email="other-therapist@example.com")
        PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PatientTherapistLink.objects.create(
                    patient=self.patient, therapist=other_therapist, requested_by=self.patient,
                    status=PatientTherapistLink.Status.ACTIVE,
                )

    def test_end_link_then_patient_can_form_new_active_link(self):
        link = PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        patient_client = auth_client(self.patient)
        end_response = patient_client.post(reverse("therapy-link-end", args=[link.id]), {"reason": "switching"})
        self.assertEqual(end_response.status_code, status.HTTP_200_OK)
        self.assertEqual(end_response.data["status"], "ended")

        other_therapist = create_therapist(email="new-therapist@example.com")
        new_link = PatientTherapistLink.objects.create(
            patient=self.patient, therapist=other_therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        self.assertEqual(new_link.status, "active")

    def test_patient_only_sees_own_links(self):
        other_patient = create_patient(email="other-patient@example.com")
        PatientTherapistLink.objects.create(
            patient=other_patient, therapist=self.therapist, requested_by=other_patient,
            status=PatientTherapistLink.Status.PENDING,
        )
        patient_client = auth_client(self.patient)
        response = patient_client.get(reverse("therapy-link-list"))
        self.assertEqual(response.data["count"], 0)
