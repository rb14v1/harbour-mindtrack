from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager

# Common IANA timezone choices offered in the UI. Any valid IANA string is
# accepted server-side (validated against zoneinfo), this is just a
# convenience default list.
COMMON_TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Dublin",
    "Europe/Berlin",
    "Asia/Kolkata",
    "Asia/Singapore",
    "Australia/Sydney",
]


class User(AbstractUser):
    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        THERAPIST = "therapist", "Therapist"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_therapist(self):
        return self.role == self.Role.THERAPIST


class PatientProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="patient_profile"
    )
    # IANA timezone name. JournalEntry.entry_date uniqueness and the
    # same-day edit window are both computed against "now" converted into
    # this timezone, never server UTC - see apps/journals/services/dates.py.
    timezone = models.CharField(max_length=64, default="UTC")
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"PatientProfile({self.user.email})"


class TherapistProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="therapist_profile"
    )
    license_number = models.CharField(max_length=64, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    specialties = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Comma-separated list of specialties, e.g. 'CBT, Anxiety, Trauma'.",
    )
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    accepting_new_patients = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TherapistProfile({self.user.email})"
