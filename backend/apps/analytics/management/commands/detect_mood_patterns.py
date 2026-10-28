"""
Nightly pattern-detection job.

Run via an OS scheduler (cron on Linux, Task Scheduler on Windows) - NOT
Celery, per the spec: the only async-ish need in this app is this single
once-a-night batch job, so adding Celery/Redis would be unjustified
infrastructure for a job this simple.

Example cron line (runs at 02:00 server time):
    0 2 * * * /path/to/venv/bin/python /path/to/backend/manage.py detect_mood_patterns

Example Windows Task Scheduler action:
    Program: C:\\path\\to\\venv\\Scripts\\python.exe
    Arguments: C:\\path\\to\\backend\\manage.py detect_mood_patterns

Upgrade path to real-time processing (documented, not built): if alerts
ever need to fire the instant a pattern completes rather than once a
night, swap this management command for a Celery Beat schedule (or keep
the command and just invoke it more frequently) - the detection functions
themselves (apps/analytics/services/trend_detection.py) don't change.
"""
from django.core.management.base import BaseCommand

from apps.analytics.services.trend_detection import run_detection_for_all_patients


class Command(BaseCommand):
    help = "Runs explicit mood-pattern detection rules for every patient and opens Alerts idempotently."

    def handle(self, *args, **options):
        created = run_detection_for_all_patients()
        if not created:
            self.stdout.write(self.style.SUCCESS("detect_mood_patterns: no new alerts."))
            return
        self.stdout.write(self.style.SUCCESS(f"detect_mood_patterns: created {len(created)} new alert(s):"))
        for alert in created:
            self.stdout.write(f"  - patient={alert.patient_id} rule={alert.rule_type} id={alert.id}")
