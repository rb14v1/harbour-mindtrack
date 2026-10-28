from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import Alert
from apps.therapy_links.models import PatientTherapistLink
from common.test_utils import auth_client, create_patient, create_therapist


class AlertWorkflowTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="alert-patient@example.com")
        self.therapist = create_therapist(email="alert-therapist@example.com")
        PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        self.therapist_client = auth_client(self.therapist)
        self.patient_client = auth_client(self.patient)

    def test_therapist_can_manually_flag_alert_for_linked_patient(self):
        response = self.therapist_client.post(reverse("alert-list"), {
            "patient": self.patient.id, "message": "Patient mentioned increased stress at work.",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["rule_type"], Alert.RuleType.THERAPIST_FLAGGED)
        self.assertEqual(response.data["triggered_by"], Alert.TriggeredBy.THERAPIST)

    def test_therapist_cannot_flag_alert_for_unlinked_patient(self):
        other_patient = create_patient(email="unlinked-alert-patient@example.com")
        response = self.therapist_client.post(reverse("alert-list"), {
            "patient": other_patient.id, "message": "nope",
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_cannot_create_alert(self):
        response = self.patient_client.post(reverse("alert-list"), {
            "patient": self.patient.id, "message": "self-flag",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_therapist_can_acknowledge_then_resolve(self):
        alert = Alert.objects.create(patient=self.patient, rule_type=Alert.RuleType.LOW_MOOD_ENTRY, message="low mood")
        ack_response = self.therapist_client.post(reverse("alert-acknowledge", args=[alert.id]))
        self.assertEqual(ack_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ack_response.data["status"], "acknowledged")

        resolve_response = self.therapist_client.post(reverse("alert-resolve", args=[alert.id]))
        self.assertEqual(resolve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(resolve_response.data["status"], "resolved")

    def test_patient_sees_own_alert_but_cannot_acknowledge(self):
        alert = Alert.objects.create(patient=self.patient, rule_type=Alert.RuleType.LOW_MOOD_ENTRY, message="low mood")
        list_response = self.patient_client.get(reverse("alert-list"))
        self.assertEqual(list_response.data["count"], 1)

        ack_response = self.patient_client.post(reverse("alert-acknowledge", args=[alert.id]))
        self.assertEqual(ack_response.status_code, status.HTTP_403_FORBIDDEN)
