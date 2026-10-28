from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import Alert
from apps.journals.models import JournalEntry, SymptomTag
from common.test_utils import auth_client, create_patient


class JournalEntryConstraintTests(APITestCase):
    def setUp(self):
        self.patient = create_patient(email="journal-patient@example.com", timezone="UTC")
        self.client_ = auth_client(self.patient)
        self.today = date.today()

    def _create_entry(self, entry_date, score=7):
        return self.client_.post(reverse("journal-entry-list"), {
            "entry_date": entry_date.isoformat(),
            "free_text_note": "Feeling okay today.",
            "mood_score": {"score": score},
        }, format="json")

    def test_one_entry_per_day_enforced(self):
        first = self._create_entry(self.today)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)

        second = self._create_entry(self.today)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(JournalEntry.objects.filter(patient=self.patient, entry_date=self.today).count(), 1)

    def test_entries_on_different_days_both_allowed(self):
        first = self._create_entry(self.today - timedelta(days=1))
        second = self._create_entry(self.today)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

    def test_future_entry_date_rejected(self):
        response = self._create_entry(self.today + timedelta(days=1))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_low_mood_score_triggers_fast_path_alert(self):
        response = self._create_entry(self.today, score=1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Alert.objects.filter(
                patient=self.patient, rule_type=Alert.RuleType.LOW_MOOD_ENTRY, status=Alert.Status.OPEN
            ).exists()
        )

    def test_fast_path_alert_is_idempotent_across_two_low_entries(self):
        self._create_entry(self.today - timedelta(days=1), score=1)
        self._create_entry(self.today, score=2)
        open_alerts = Alert.objects.filter(
            patient=self.patient, rule_type=Alert.RuleType.LOW_MOOD_ENTRY, status=Alert.Status.OPEN
        )
        self.assertEqual(open_alerts.count(), 1)

    def test_normal_mood_score_does_not_trigger_alert(self):
        self._create_entry(self.today, score=8)
        self.assertFalse(Alert.objects.filter(rule_type=Alert.RuleType.LOW_MOOD_ENTRY).exists())

    def test_same_day_edit_allowed_and_history_preserved(self):
        create_response = self._create_entry(self.today, score=6)
        entry_id = create_response.data["id"]

        patch_response = self.client_.patch(
            reverse("journal-entry-detail", args=[entry_id]),
            {"free_text_note": "Updated note.", "mood_score": {"score": 7}},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK, patch_response.data)
        entry = JournalEntry.objects.get(id=entry_id)
        self.assertEqual(entry.free_text_note, "Updated note.")
        self.assertEqual(entry.edit_count, 1)
        self.assertEqual(entry.edit_history.count(), 1)
        self.assertEqual(entry.edit_history.first().previous_free_text_note, "Feeling okay today.")

    def test_edit_outside_same_day_window_rejected(self):
        entry = JournalEntry.objects.create(
            patient=self.patient, entry_date=self.today - timedelta(days=2), free_text_note="old"
        )
        from apps.journals.models import MoodScore
        MoodScore.objects.create(entry=entry, score=5)

        patch_response = self.client_.patch(
            reverse("journal-entry-detail", args=[entry.id]),
            {"free_text_note": "trying to edit later"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_symptom_tags_can_be_attached(self):
        tag = SymptomTag.objects.filter(name="Anxiety").first()
        self.assertIsNotNone(tag, "Expected seeded symptom tags from data migration")
        response = self.client_.post(reverse("journal-entry-list"), {
            "entry_date": self.today.isoformat(),
            "free_text_note": "Anxious today.",
            "mood_score": {"score": 5},
            "symptoms": [{"symptom": tag.id, "severity": 3}],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(len(response.data["symptoms"]), 1)

    def test_patient_cannot_create_entry_for_another_patient(self):
        other_patient = create_patient(email="other-journal-patient@example.com")
        response = self.client_.post(reverse("journal-entry-list"), {
            "patient": other_patient.id,
            "entry_date": self.today.isoformat(),
            "mood_score": {"score": 5},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        entry = JournalEntry.objects.get(id=response.data["id"])
        # `patient` is a read-only field: the view always forces it to the
        # authenticated requester regardless of what's posted.
        self.assertEqual(entry.patient_id, self.patient.id)

    def test_symptom_tag_lookup_is_readonly_and_listable(self):
        response = self.client_.get(reverse("symptom-tag-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
