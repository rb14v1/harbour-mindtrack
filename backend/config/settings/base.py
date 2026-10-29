"""
Base settings shared by all environments.
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Secrets must be supplied by the environment (injected from the secret store,
# e.g. Azure Key Vault). No fallback defaults are provided on purpose: a missing
# value raises at startup rather than silently running with a known credential.
SECRET_KEY = config("DJANGO_SECRET_KEY")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    # local apps
    "apps.accounts",
    "apps.therapy_links",
    "apps.journals",
    "apps.therapy_notes",
    "apps.analytics",
    "apps.audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
#
# Real deployments (docker-compose / prod) use Postgres - see
# docker-compose.yml and .env.example. Nothing in this app relies on a
# Postgres-only feature (no exclusion constraints etc.), so the dev-only
# SQLite override below is sufficient to run the full test suite without a
# local Postgres/Docker install.
#
# DEV-ONLY OVERRIDE: when USE_SQLITE=True is set in the environment, fall
# back to SQLite so `manage.py check`, `makemigrations` and `test` can run on
# a machine with no Postgres/Docker available. This is NOT part of the
# supported runtime configuration for real deployments.
# ---------------------------------------------------------------------------
USE_SQLITE = config("USE_SQLITE", default=False, cast=bool)

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev-sqlite.db",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="mindtrack"),
            "USER": config("POSTGRES_USER", default="mindtrack"),
            # No default: must come from the environment / secret store.
            "PASSWORD": config("POSTGRES_PASSWORD"),
            "HOST": config("POSTGRES_HOST", default="localhost"),
            "PORT": config("POSTGRES_PORT", default="5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# MindTrack-specific settings
# ---------------------------------------------------------------------------

# Threshold (inclusive) at which a single journal entry's mood score
# triggers an immediate, synchronous "low_mood_entry" alert. See
# apps/journals/services/alerts.py.
LOW_MOOD_FAST_PATH_THRESHOLD = config("LOW_MOOD_FAST_PATH_THRESHOLD", default=2, cast=int)

# Trend-detection rule thresholds. See apps/analytics/services/trend_detection.py
# for the full, explainable rule set (no ML/black-box scoring - every alert
# traces back to one of these named, documented rules).
TREND_MEAN_MOOD_WINDOW_DAYS = config("TREND_MEAN_MOOD_WINDOW_DAYS", default=7, cast=int)
TREND_MEAN_MOOD_THRESHOLD = config("TREND_MEAN_MOOD_THRESHOLD", default=3, cast=int)
TREND_CONSECUTIVE_LOW_MOOD_COUNT = config("TREND_CONSECUTIVE_LOW_MOOD_COUNT", default=3, cast=int)
TREND_CONSECUTIVE_LOW_MOOD_THRESHOLD = config("TREND_CONSECUTIVE_LOW_MOOD_THRESHOLD", default=2, cast=int)
TREND_NO_ENTRY_STREAK_DAYS = config("TREND_NO_ENTRY_STREAK_DAYS", default=5, cast=int)

# Patients may only edit a journal entry on the same local calendar day it
# was created (per the patient's stored timezone). After that window the
# entry becomes part of the clinical record and is read-only; prior edits
# within the window are preserved in JournalEntryEdit for audit purposes.
JOURNAL_SAME_DAY_EDIT_WINDOW = True
