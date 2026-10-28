"""
Timezone-aware date helpers.

Per spec: "entry-date uniqueness uses patient's timezone, not server UTC".
Every place that needs "what day is it for this patient right now" goes
through `patient_local_today`/`patient_local_now` rather than
`date.today()`/`timezone.now().date()`, which would use the server's UTC
clock and could put an entry on the wrong day for a patient in, say,
Australia/Sydney.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone


def _tzinfo(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def patient_local_now(patient_profile) -> datetime:
    """Current instant, converted into the patient's stored IANA timezone."""
    return timezone.now().astimezone(_tzinfo(patient_profile.timezone))


def patient_local_today(patient_profile) -> date:
    """Today's calendar date in the patient's stored timezone."""
    return patient_local_now(patient_profile).date()
