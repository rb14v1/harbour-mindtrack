"""
Cross-therapist data isolation.

Proves that Therapist A, who has no link at all to Therapist B's patient,
cannot retrieve that patient's journal entries, mood trend, symptom
frequency, or session notes - by ID guessing (direct object id) or by
driving the patient-scoped analytics URLs directly. Every endpoint must
return 404 (not 403, so existence can't be inferred either), because the
underlying queryset is structurally scoped to
`active_patient_ids_for_therapist(request.user)` rather than relying on a
serializer-only hide.
"""
from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.journals.models import JournalEntry, MoodScore
from apps.therapy_links.models import PatientTherapistLink
from apps.therapy_notes.models import SessionNote
from common.test_utils import auth_client, create_patient, create_therapist


class CrossTherapistIsolationTests(APITestCase):
    def setUp(self):
        self.patient_b = create_patient(email="patient-b@example.com")
        self.therapist_a = create_therapist(email="therapist-a@example.com")
        self.therapist_b = create_therapist(email="therapist-b@example.com")

        # Only therapist B is actively linked to patient B.
        PatientTherapistLink.objects.create(
            patient=self.patient_b, therapist=self.therapist_b, requested_by=self.patient_b,
            status=PatientTherapistLink.Status.ACTIVE,
        )

        self.entry = JournalEntry.objects.create(
            patient=self.patient_b, entry_date=date.today(), free_text_note="private note"
        )
        MoodScore.objects.create(entry=self.entry, score=6)

        self.note = SessionNote.objects.create(
            patient=self.patient_b, therapist=self.therapist_b, session_date=date.today(),
            note_text="confidential session content", visible_to_patient=True,
        )

        self.client_a = auth_client(self.therapist_a)
        self.client_b = auth_client(self.therapist_b)

    def test_unlinked_therapist_cannot_list_patients_journal_entries(self):
        response = self.client_a.get(reverse("journal-entry-list"), {"patient": self.patient_b.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_unlinked_therapist_cannot_retrieve_journal_entry_by_id(self):
        response = self.client_a.get(reverse("journal-entry-detail", args=[self.entry.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_linked_therapist_can_retrieve_journal_entry(self):
        response = self.client_b.get(reverse("journal-entry-detail", args=[self.entry.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unlinked_therapist_cannot_fetch_trend_by_patient_id_guessing(self):
        response = self.client_a.get(reverse("patient-trend", args=[self.patient_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_linked_therapist_can_fetch_trend(self):
        response = self.client_b.get(reverse("patient-trend", args=[self.patient_b.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unlinked_therapist_cannot_fetch_symptom_frequency(self):
        response = self.client_a.get(reverse("patient-symptom-frequency", args=[self.patient_b.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unlinked_therapist_cannot_retrieve_session_note_by_id(self):
        response = self.client_a.get(reverse("therapy-note-detail", args=[self.note.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unlinked_therapist_cannot_create_note_for_unlinked_patient(self):
        response = self.client_a.post(reverse("therapy-note-list"), {
            "patient": self.patient_b.id,
            "session_date": date.today().isoformat(),
            "note_text": "trying to sneak a note in",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(SessionNote.objects.filter(note_text="trying to sneak a note in").exists())

    def test_unlinked_therapist_not_in_dashboard_for_patient_b(self):
        response = self.client_a.get(reverse("therapist-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        patient_ids = [row["patient"] for row in response.data["patients"]]
        self.assertNotIn(self.patient_b.id, patient_ids)

    def test_unlinked_therapist_cannot_see_alerts_for_patient_b(self):
        from apps.analytics.models import Alert
        Alert.objects.create(patient=self.patient_b, rule_type=Alert.RuleType.LOW_MOOD_ENTRY, message="test")
        response = self.client_a.get(reverse("alert-list"))
        self.assertEqual(response.data["count"], 0)
