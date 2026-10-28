from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.analytics.models import Alert
from apps.analytics.services.trend_detection import (
    check_consecutive_low_mood,
    check_low_mean_mood,
    check_no_entry_streak,
    run_detection_for_patient,
)
from apps.journals.models import JournalEntry, MoodScore
from common.test_utils import create_patient


def _make_entry(patient, days_ago, score):
    entry = JournalEntry.objects.create(patient=patient, entry_date=date.today() - timedelta(days=days_ago))
    MoodScore.objects.create(entry=entry, score=score)
    return entry


class LowMeanMoodRuleTests(TestCase):
    def test_triggers_when_mean_at_or_below_threshold(self):
        patient = create_patient(email="mean-mood@example.com")
        for i in range(7):
            _make_entry(patient, i, 3)
        result = check_low_mean_mood(patient)
        self.assertTrue(result.triggered)

    def test_does_not_trigger_when_mean_above_threshold(self):
        patient = create_patient(email="mean-mood-2@example.com")
        for i in range(7):
            _make_entry(patient, i, 8)
        result = check_low_mean_mood(patient)
        self.assertFalse(result.triggered)

    def test_ignores_entries_outside_window(self):
        patient = create_patient(email="mean-mood-3@example.com")
        _make_entry(patient, 30, 1)  # outside the default 7-day window
        result = check_low_mean_mood(patient)
        self.assertFalse(result.triggered)


class ConsecutiveLowMoodRuleTests(TestCase):
    def test_triggers_on_three_consecutive_low_entries(self):
        patient = create_patient(email="consecutive@example.com")
        _make_entry(patient, 2, 2)
        _make_entry(patient, 1, 1)
        _make_entry(patient, 0, 2)
        result = check_consecutive_low_mood(patient)
        self.assertTrue(result.triggered)

    def test_does_not_trigger_if_one_entry_breaks_the_streak(self):
        patient = create_patient(email="consecutive-2@example.com")
        _make_entry(patient, 2, 2)
        _make_entry(patient, 1, 9)
        _make_entry(patient, 0, 2)
        result = check_consecutive_low_mood(patient)
        self.assertFalse(result.triggered)


class NoEntryStreakRuleTests(TestCase):
    def test_triggers_when_no_entries_in_window(self):
        patient = create_patient(email="no-entry@example.com")
        # created_at is auto_now_add, so backdate it via a queryset .update()
        # (a normal instance .save() would not override it).
        from apps.accounts.models import PatientProfile
        PatientProfile.objects.filter(user=patient).update(created_at=timezone.now() - timedelta(days=30))
        # Django caches the reverse one-to-one accessor on `patient` from
        # when the profile was created, which the .update() above bypasses
        # - force a fresh fetch so the rule sees the backdated profile.
        patient.refresh_from_db()

        result = check_no_entry_streak(patient)
        self.assertTrue(result.triggered)

    def test_does_not_trigger_for_brand_new_patient(self):
        patient = create_patient(email="brand-new@example.com")
        result = check_no_entry_streak(patient)
        self.assertFalse(result.triggered)

    def test_does_not_trigger_when_recent_entry_exists(self):
        patient = create_patient(email="has-entry@example.com")
        from apps.accounts.models import PatientProfile
        PatientProfile.objects.filter(user=patient).update(created_at=timezone.now() - timedelta(days=30))
        patient.refresh_from_db()
        _make_entry(patient, 1, 5)
        result = check_no_entry_streak(patient)
        self.assertFalse(result.triggered)


class IdempotentAlertingTests(TestCase):
    def test_running_detection_twice_does_not_duplicate_open_alert(self):
        patient = create_patient(email="idempotent@example.com")
        for i in range(7):
            _make_entry(patient, i, 2)

        first_run = run_detection_for_patient(patient)
        self.assertGreater(len(first_run), 0)

        second_run = run_detection_for_patient(patient)
        self.assertEqual(len(second_run), 0, "Second run must not create duplicate alerts.")

        open_mean_mood_alerts = Alert.objects.filter(
            patient=patient, rule_type=Alert.RuleType.LOW_MEAN_MOOD_7D, status=Alert.Status.OPEN
        )
        self.assertEqual(open_mean_mood_alerts.count(), 1)

    def test_resolved_alert_allows_a_new_one_to_open(self):
        patient = create_patient(email="idempotent-2@example.com")
        for i in range(7):
            _make_entry(patient, i, 2)
        run_detection_for_patient(patient)

        alert = Alert.objects.get(patient=patient, rule_type=Alert.RuleType.LOW_MEAN_MOOD_7D)
        alert.status = Alert.Status.RESOLVED
        alert.save()

        second_run = run_detection_for_patient(patient)
        self.assertEqual(len(second_run), 1)
        self.assertEqual(
            Alert.objects.filter(patient=patient, rule_type=Alert.RuleType.LOW_MEAN_MOOD_7D, status=Alert.Status.OPEN).count(),
            1,
        )
