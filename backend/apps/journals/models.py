from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SymptomTag(models.Model):
    """Lookup table of selectable symptoms, e.g. Anxiety, Insomnia, Fatigue."""

    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class JournalEntry(models.Model):
    """One entry per patient per calendar day (in the patient's own
    timezone - see services/dates.py). Mood score and symptoms are separate
    related models (MoodScore is 1:1, symptoms are M2M-through), but are
    almost always created/fetched together, see serializers.py."""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="journal_entries"
    )
    entry_date = models.DateField()
    free_text_note = models.TextField(blank=True, default="")

    # Out-of-scope hardening note (see README): in a real deployment,
    # free_text_note (and SessionNote.note_text) should be encrypted at the
    # field level (e.g. via a library like django-cryptography) in addition
    # to disk-level Postgres encryption. Left as plaintext here to keep the
    # demo's ORM/filtering/tests straightforward.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    edit_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["patient", "entry_date"], name="unique_entry_per_patient_per_day"),
        ]
        ordering = ["-entry_date"]
        indexes = [models.Index(fields=["patient", "entry_date"])]

    def __str__(self):
        return f"JournalEntry({self.patient_id}, {self.entry_date})"


class JournalEntryEdit(models.Model):
    """Snapshot of a JournalEntry's content immediately before an edit was
    applied, preserved for clinical-record integrity (spec: 'edit history
    preserved')."""

    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="edit_history")
    previous_free_text_note = models.TextField(blank=True, default="")
    previous_mood_score = models.PositiveSmallIntegerField(null=True, blank=True)
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-edited_at"]


class MoodScore(models.Model):
    entry = models.OneToOneField(JournalEntry, on_delete=models.CASCADE, related_name="mood_score")
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    energy_level = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    sleep_hours = models.DecimalField(null=True, blank=True, max_digits=4, decimal_places=1)

    def __str__(self):
        return f"MoodScore(entry={self.entry_id}, score={self.score})"


class JournalEntrySymptom(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="symptoms")
    symptom = models.ForeignKey(SymptomTag, on_delete=models.PROTECT, related_name="entries")
    severity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["entry", "symptom"], name="unique_symptom_per_entry"),
        ]
