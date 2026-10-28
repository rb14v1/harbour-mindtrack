from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.journals.models import JournalEntry, JournalEntryEdit, JournalEntrySymptom, MoodScore, SymptomTag
from apps.journals.services.alerts import check_low_mood_fast_path
from apps.journals.services.dates import patient_local_today


class SymptomTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomTag
        fields = ["id", "name", "description", "is_active"]


class MoodScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodScore
        fields = ["score", "energy_level", "sleep_hours"]


class JournalEntrySymptomSerializer(serializers.ModelSerializer):
    symptom_name = serializers.CharField(source="symptom.name", read_only=True)

    class Meta:
        model = JournalEntrySymptom
        fields = ["id", "symptom", "symptom_name", "severity"]


class JournalEntryEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalEntryEdit
        fields = ["id", "previous_free_text_note", "previous_mood_score", "edited_at", "edited_by"]


class JournalEntrySerializer(serializers.ModelSerializer):
    """Nested read/write serializer: a journal entry is created and edited
    together with its mood score and symptom list in one request, which
    keeps "one entry per day" semantics simple for the frontend (a single
    form submit) and lets the fast-path alert check run against the
    complete picture (it needs the mood score)."""

    mood_score = MoodScoreSerializer()
    symptoms = JournalEntrySymptomSerializer(many=True, required=False)
    edit_history = JournalEntryEditSerializer(many=True, read_only=True)
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = [
            "id", "patient", "entry_date", "free_text_note",
            "mood_score", "symptoms", "edit_history",
            "created_at", "updated_at", "last_edited_at", "edit_count",
            "is_editable",
        ]
        read_only_fields = [
            "id", "patient", "created_at", "updated_at", "last_edited_at", "edit_count", "edit_history",
        ]

    def get_is_editable(self, obj: JournalEntry) -> bool:
        if not getattr(settings, "JOURNAL_SAME_DAY_EDIT_WINDOW", True):
            return True
        profile = getattr(obj.patient, "patient_profile", None)
        if profile is None:
            return False
        return obj.entry_date == patient_local_today(profile)

    def validate_entry_date(self, value):
        request = self.context["request"]
        profile = getattr(request.user, "patient_profile", None)
        if profile is None:
            raise serializers.ValidationError("No patient profile found for this user.")
        today = patient_local_today(profile)
        if value > today:
            raise serializers.ValidationError("Cannot create a journal entry for a future date.")

        # Belt-and-braces: the DB-level UniqueConstraint is the source of
        # truth, but checking here lets us return a clean 400 instead of an
        # uncaught IntegrityError turning into a 500.
        existing = JournalEntry.objects.filter(patient=request.user, entry_date=value)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("You already have a journal entry for this date.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        mood_data = validated_data.pop("mood_score")
        symptoms_data = validated_data.pop("symptoms", [])
        request = self.context["request"]
        validated_data["patient"] = request.user

        entry = JournalEntry.objects.create(**validated_data)
        mood_score = MoodScore.objects.create(entry=entry, **mood_data)
        for symptom_item in symptoms_data:
            JournalEntrySymptom.objects.create(entry=entry, **symptom_item)

        check_low_mood_fast_path(entry, mood_score)
        return entry

    @transaction.atomic
    def update(self, instance: JournalEntry, validated_data):
        if not self.get_is_editable(instance):
            raise serializers.ValidationError(
                "This entry is outside its same-day edit window and is now part of the fixed clinical record."
            )

        mood_data = validated_data.pop("mood_score", None)
        symptoms_data = validated_data.pop("symptoms", None)

        previous_mood = getattr(instance, "mood_score", None)
        JournalEntryEdit.objects.create(
            entry=instance,
            previous_free_text_note=instance.free_text_note,
            previous_mood_score=previous_mood.score if previous_mood else None,
            edited_by=self.context["request"].user,
        )

        instance.free_text_note = validated_data.get("free_text_note", instance.free_text_note)
        instance.edit_count += 1
        from django.utils import timezone as dj_timezone
        instance.last_edited_at = dj_timezone.now()
        instance.save()

        mood_score = previous_mood
        if mood_data is not None:
            if previous_mood is not None:
                for key, value in mood_data.items():
                    setattr(previous_mood, key, value)
                previous_mood.save()
                mood_score = previous_mood
            else:
                mood_score = MoodScore.objects.create(entry=instance, **mood_data)

        if symptoms_data is not None:
            instance.symptoms.all().delete()
            for symptom_item in symptoms_data:
                JournalEntrySymptom.objects.create(entry=instance, **symptom_item)

        if mood_score is not None:
            check_low_mood_fast_path(instance, mood_score)

        return instance
