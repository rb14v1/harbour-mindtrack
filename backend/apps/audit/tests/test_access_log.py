from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AccessLog
from apps.journals.models import JournalEntry, MoodScore
from apps.therapy_links.models import PatientTherapistLink
from common.test_utils import auth_client, create_patient, create_therapist


class AccessLogTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="audit-patient@example.com")
        self.therapist = create_therapist(email="audit-therapist@example.com")
        PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        entry = JournalEntry.objects.create(patient=self.patient, entry_date=date.today())
        MoodScore.objects.create(entry=entry, score=5)
        self.entry = entry
        self.therapist_client = auth_client(self.therapist)
        self.patient_client = auth_client(self.patient)

    def test_therapist_retrieving_journal_entry_writes_access_log(self):
        self.assertEqual(AccessLog.objects.count(), 0)
        response = self.therapist_client.get(reverse("journal-entry-detail", args=[self.entry.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        log = AccessLog.objects.get()
        self.assertEqual(log.actor_id, self.therapist.id)
        self.assertEqual(log.patient_id, self.patient.id)
        self.assertEqual(log.action, AccessLog.Action.JOURNAL_VIEW)

    def test_therapist_viewing_trend_writes_access_log(self):
        response = self.therapist_client.get(reverse("patient-trend", args=[self.patient.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AccessLog.objects.filter(actor=self.therapist, patient=self.patient, action=AccessLog.Action.TREND_VIEW).exists()
        )

    def test_therapist_viewing_symptom_frequency_writes_access_log(self):
        response = self.therapist_client.get(reverse("patient-symptom-frequency", args=[self.patient.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AccessLog.objects.filter(
                actor=self.therapist, patient=self.patient, action=AccessLog.Action.SYMPTOM_FREQUENCY_VIEW
            ).exists()
        )

    def test_patient_viewing_own_trend_does_not_write_access_log(self):
        response = self.patient_client.get(reverse("patient-trend", args=[self.patient.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AccessLog.objects.count(), 0)

    def test_patient_viewing_own_journal_does_not_write_access_log(self):
        response = self.patient_client.get(reverse("journal-entry-detail", args=[self.entry.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AccessLog.objects.count(), 0)
