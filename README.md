# MindTrack - Mental Health Journaling

A patient journaling + therapist review app: patients log daily mood/symptom
entries, therapists (once linked) review trends and leave session notes, and
an explicit, explainable rule engine raises alerts on concerning patterns.

Stack: React + Vite + TypeScript, Django REST Framework, PostgreSQL. No
Celery/Redis - the only async-ish need (nightly pattern detection) runs as a
Django management command via an OS scheduler.

## Running with Docker (requires Docker)

```
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py createsuperuser
```

- Backend: http://localhost:8000/api/
- Frontend: http://localhost:5173/
- Admin: http://localhost:8000/admin/

## Running the backend without Docker (dev-only SQLite override)

This machine had no local Docker/Postgres available during development, so
the backend supports a documented, dev-only SQLite fallback (same pattern as
the sibling `appointment-referral-hub` app). **Never use this for a real
deployment** - it exists purely so `manage.py check/makemigrations/test` can
run without Postgres.

```
cd backend
python -m venv venv
./venv/Scripts/activate        # or source venv/bin/activate on macOS/Linux
pip install -r requirements.txt

set USE_SQLITE=True            # PowerShell: $env:USE_SQLITE="True"
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Nightly pattern-detection job

`python manage.py detect_mood_patterns` runs the explicit trend-detection
rules (see `apps/analytics/services/trend_detection.py`) for every patient
and idempotently opens Alerts. Schedule it once nightly via cron or Windows
Task Scheduler - see the docstring at the top of
`apps/analytics/management/commands/detect_mood_patterns.py` for example
invocations. No Celery/Redis is used anywhere in this app.

## Security/privacy notes (hardening out of scope for this build)

- `JournalEntry.free_text_note` and `SessionNote.note_text` are stored as
  plaintext in this demo. A real deployment should add field-level
  encryption (e.g. via `django-cryptography`) on top of disk-level Postgres
  encryption (e.g. managed-Postgres encryption-at-rest, or `pgcrypto`).
- JWT access tokens live in memory only on the frontend; refresh tokens are
  kept in `localStorage` for this demo (a real deployment would prefer an
  httpOnly cookie, which needs a same-site or proxied backend+frontend
  origin).
- Auth endpoints (`register`, `login`, `refresh`, `logout`) are throttled via
  DRF's `ScopedRateThrottle` (`auth` scope, 20/min by default).

## Data isolation

Therapist access to patient data is scoped at the **queryset** level, not
via serializer hiding - see `apps/therapy_links/permissions.py`
(`active_patient_ids_for_therapist`) and its use in
`apps/journals/views.py`, `apps/therapy_notes/views.py`, and
`apps/analytics/views.py`. Every therapist GET of a patient's journal
entries, mood trend, or symptom frequency writes an `AccessLog` row (see
`apps/audit/models.py`).

## Deviations from the original spec (and why)

- Alert acknowledgement/resolution workflow uses two explicit actions
  (`acknowledge`, `resolve`) rather than a single generic PATCH, to keep the
  state transitions auditable (who/when) without a bespoke state machine
  for what is really just a two-step lifecycle.
- `requirements.txt` is a single file (base + dev/test deps together)
  rather than split `base/dev/prod` files, since this app has no
  prod-specific extra dependencies beyond `gunicorn` - kept everything in
  one file for a smaller surface area on a from-scratch build.
