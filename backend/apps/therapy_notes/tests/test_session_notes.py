from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.therapy_links.models import PatientTherapistLink
from apps.therapy_notes.models import SessionNote
from common.test_utils import auth_client, create_patient, create_therapist


class SessionNoteVisibilityTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="note-patient@example.com")
        self.therapist = create_therapist(email="note-therapist@example.com")
        self.link = PatientTherapistLink.objects.create(
            patient=self.patient, therapist=self.therapist, requested_by=self.patient,
            status=PatientTherapistLink.Status.ACTIVE,
        )
        self.visible_note = SessionNote.objects.create(
            patient=self.patient, therapist=self.therapist, link=self.link, session_date=date.today(),
            note_text="Shared with patient.", visible_to_patient=True,
        )
        self.private_note = SessionNote.objects.create(
            patient=self.patient, therapist=self.therapist, link=self.link, session_date=date.today(),
            note_text="Private clinical impression.", visible_to_patient=False,
        )

    def test_patient_sees_only_visible_notes(self):
        client = auth_client(self.patient)
        response = client.get(reverse("therapy-note-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.visible_note.id, ids)
        self.assertNotIn(self.private_note.id, ids)

    def test_patient_cannot_retrieve_private_note_by_id(self):
        client = auth_client(self.patient)
        response = client.get(reverse("therapy-note-detail", args=[self.private_note.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_facing_serializer_never_exposes_visible_to_patient_write_path(self):
        client = auth_client(self.patient)
        response = client.get(reverse("therapy-note-detail", args=[self.visible_note.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("visible_to_patient", response.data)

    def test_therapist_sees_both_notes(self):
        client = auth_client(self.therapist)
        response = client.get(reverse("therapy-note-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.visible_note.id, ids)
        self.assertIn(self.private_note.id, ids)

    def test_patient_cannot_create_session_note(self):
        client = auth_client(self.patient)
        response = client.post(reverse("therapy-note-list"), {
            "patient": self.patient.id, "session_date": date.today().isoformat(), "note_text": "nope",
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_note_requires_active_link(self):
        other_patient = create_patient(email="unlinked-patient@example.com")
        client = auth_client(self.therapist)
        response = client.post(reverse("therapy-note-list"), {
            "patient": other_patient.id, "session_date": date.today().isoformat(), "note_text": "no link exists",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_historical_note_visibility_preserved_after_link_ends(self):
        self.link.status = PatientTherapistLink.Status.ENDED
        self.link.save(update_fields=["status"])

        patient_client = auth_client(self.patient)
        response = patient_client.get(reverse("therapy-note-list"))
        ids = [row["id"] for row in response.data["results"]]
        self.assertIn(self.visible_note.id, ids, "Previously-visible notes must remain visible after the link ends.")

        # But live dashboard-style journal/trend access is now blocked for
        # the therapist, since the link is no longer active.
        therapist_client = auth_client(self.therapist)
        trend_response = therapist_client.get(reverse("patient-trend", args=[self.patient.id]))
        self.assertEqual(trend_response.status_code, status.HTTP_404_NOT_FOUND)

        # The therapist can still see the note they authored historically.
        notes_response = therapist_client.get(reverse("therapy-note-list"))
        note_ids = [row["id"] for row in notes_response.data["results"]]
        self.assertIn(self.visible_note.id, note_ids)
