"""
Fast-path (synchronous) alerting.

This runs inline when a journal entry + mood score is saved - distinct from
the nightly trend-detection job in apps.analytics.services.trend_detection,
which looks at multi-day patterns. This one rule fires immediately so a
single very-low mood score doesn't wait for the next scheduled run.

Rule (explicit, explainable): score <= settings.LOW_MOOD_FAST_PATH_THRESHOLD
-> open an Alert of rule_type 'low_mood_entry' for the patient, unless one
is already open (idempotent).

Import of apps.analytics.models is done lazily inside the function to avoid
a module-level import cycle between journals and analytics.
"""
from django.conf import settings


def check_low_mood_fast_path(journal_entry, mood_score) -> "object | None":
    from apps.analytics.models import Alert

    threshold = getattr(settings, "LOW_MOOD_FAST_PATH_THRESHOLD", 2)
    if mood_score.score > threshold:
        return None

    already_open = Alert.objects.filter(
        patient=journal_entry.patient,
        rule_type=Alert.RuleType.LOW_MOOD_ENTRY,
        status=Alert.Status.OPEN,
    ).exists()
    if already_open:
        return None

    return Alert.objects.create(
        patient=journal_entry.patient,
        rule_type=Alert.RuleType.LOW_MOOD_ENTRY,
        triggered_by=Alert.TriggeredBy.SYSTEM,
        source_entry=journal_entry,
        message=(
            f"Mood score of {mood_score.score} recorded on {journal_entry.entry_date} "
            f"is at or below the fast-path threshold ({threshold})."
        ),
    )
