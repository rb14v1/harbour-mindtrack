"""
Explicit, explainable pattern-detection rules for the nightly
`detect_mood_patterns` job (see
apps/analytics/management/commands/detect_mood_patterns.py).

Design intent (spec requirement): NO ML, NO black-box scoring. Every rule
here is a short, named, documented condition over plain aggregates that a
clinician (or a test) can verify by hand. Each rule returns a `RuleResult`
describing exactly why it did or did not trigger, and
`run_detection_for_patient` is idempotent - it will never create a second
OPEN alert of the same rule_type for the same patient (checked explicitly
here AND enforced by a partial unique DB constraint on Alert, so even a
racing concurrent run cannot duplicate one).

Three rules, matching the plan:
  1. low_mean_mood_7d:      mean(mood score) over the trailing N days <= threshold.
  2. consecutive_low_mood:  the most recent N journal entries are ALL <= threshold.
  3. no_entry_streak:       zero journal entries in the trailing N-day window
                             (only evaluated once the patient has been
                             enrolled for at least that many days, so a
                             brand-new patient isn't immediately flagged).

This module exposes plain functions so it can be called directly/
synchronously from tests or other code; `detect_mood_patterns` is the
thin management-command wrapper meant to be invoked by an OS scheduler
(cron / Windows Task Scheduler) once nightly - no Celery/Redis per the
spec, since this is the only async-ish need in the whole app.
"""
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from apps.analytics.models import Alert
from apps.journals.models import JournalEntry
from apps.journals.services.dates import patient_local_today


@dataclass
class RuleResult:
    rule_type: str
    triggered: bool
    detail: str


def _local_today(patient):
    profile = getattr(patient, "patient_profile", None)
    if profile is not None:
        return patient_local_today(profile)
    return timezone.now().date()


def check_low_mean_mood(patient, window_days=None, threshold=None) -> RuleResult:
    """Rule: mean(mood score) over the trailing `window_days` (inclusive of
    today) is <= `threshold`. Entries with no mood score are ignored, not
    treated as zero."""
    window_days = window_days or settings.TREND_MEAN_MOOD_WINDOW_DAYS
    threshold = settings.TREND_MEAN_MOOD_THRESHOLD if threshold is None else threshold
    today = _local_today(patient)
    start = today - timedelta(days=window_days - 1)

    scores = list(
        JournalEntry.objects.filter(
            patient=patient, entry_date__gte=start, entry_date__lte=today, mood_score__isnull=False
        ).values_list("mood_score__score", flat=True)
    )
    if not scores:
        return RuleResult(Alert.RuleType.LOW_MEAN_MOOD_7D, False, "No scored entries in window.")

    mean_score = sum(scores) / len(scores)
    triggered = mean_score <= threshold
    detail = (
        f"Mean mood across {len(scores)} entries between {start} and {today} is "
        f"{mean_score:.2f} (rule triggers at <= {threshold})."
    )
    return RuleResult(Alert.RuleType.LOW_MEAN_MOOD_7D, triggered, detail)


def check_consecutive_low_mood(patient, count=None, threshold=None) -> RuleResult:
    """Rule: the most recent `count` journal entries (by entry_date, most
    recent first) all have a mood score <= `threshold`. Requires at least
    `count` scored entries to exist at all."""
    count = count or settings.TREND_CONSECUTIVE_LOW_MOOD_COUNT
    threshold = settings.TREND_CONSECUTIVE_LOW_MOOD_THRESHOLD if threshold is None else threshold

    recent = list(
        JournalEntry.objects.filter(patient=patient, mood_score__isnull=False)
        .order_by("-entry_date")
        .values_list("entry_date", "mood_score__score")[:count]
    )
    triggered = len(recent) == count and all(score <= threshold for _, score in recent)
    detail = (
        f"Most recent {len(recent)} scored entries: {recent} "
        f"(rule triggers when {count} most recent entries are all <= {threshold})."
    )
    return RuleResult(Alert.RuleType.CONSECUTIVE_LOW_MOOD, triggered, detail)


def check_no_entry_streak(patient, days=None) -> RuleResult:
    """Rule: zero journal entries in the trailing `days`-day window. Skipped
    (never triggers) if the patient's profile is younger than the window,
    so a patient who joined yesterday isn't immediately flagged for "not
    journaling" over a window that predates their account."""
    days = days or settings.TREND_NO_ENTRY_STREAK_DAYS
    today = _local_today(patient)
    start = today - timedelta(days=days - 1)

    profile = getattr(patient, "patient_profile", None)
    if profile is not None and profile.created_at.date() > start:
        return RuleResult(
            Alert.RuleType.NO_ENTRY_STREAK, False, "Patient profile is younger than the lookback window."
        )

    has_entry = JournalEntry.objects.filter(patient=patient, entry_date__gte=start, entry_date__lte=today).exists()
    triggered = not has_entry
    detail = f"No journal entries between {start} and {today} ({days}-day window)." if triggered else "Entry found in window."
    return RuleResult(Alert.RuleType.NO_ENTRY_STREAK, triggered, detail)


ALL_RULES = (check_low_mean_mood, check_consecutive_low_mood, check_no_entry_streak)


def _ensure_open_alert(patient, rule_type: str, message: str):
    """Idempotent alert creation: returns (alert, created)."""
    existing = Alert.objects.filter(patient=patient, rule_type=rule_type, status=Alert.Status.OPEN).first()
    if existing:
        return existing, False
    try:
        alert = Alert.objects.create(
            patient=patient,
            rule_type=rule_type,
            triggered_by=Alert.TriggeredBy.SYSTEM,
            message=message,
        )
        return alert, True
    except IntegrityError:
        # Lost a race against a concurrent detection run; the other run's
        # alert is already open, so just return it.
        return Alert.objects.get(patient=patient, rule_type=rule_type, status=Alert.Status.OPEN), False


def run_detection_for_patient(patient) -> list:
    """Runs every rule for one patient, returns the list of newly-created
    Alert instances (empty if nothing triggered, or everything that
    triggered already had an open alert)."""
    created = []
    for rule in ALL_RULES:
        result = rule(patient)
        if result.triggered:
            alert, was_created = _ensure_open_alert(patient, result.rule_type, result.detail)
            if was_created:
                created.append(alert)
    return created


def run_detection_for_all_patients() -> list:
    from apps.accounts.models import PatientProfile

    created = []
    for profile in PatientProfile.objects.select_related("user"):
        created.extend(run_detection_for_patient(profile.user))
    return created
