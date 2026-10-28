from rest_framework import serializers

from apps.analytics.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id", "patient", "patient_email", "rule_type", "status", "triggered_by",
            "created_by", "source_entry", "message", "created_at",
            "acknowledged_at", "acknowledged_by", "resolved_at", "resolved_by",
        ]
        read_only_fields = [
            "id", "patient_email", "status", "triggered_by", "created_by", "source_entry",
            "created_at", "acknowledged_at", "acknowledged_by", "resolved_at", "resolved_by",
        ]


class CreateManualAlertSerializer(serializers.Serializer):
    """A therapist manually flagging a concern about a linked patient -
    rule_type is always THERAPIST_FLAGGED for these (the system rule types
    are reserved for the automated checks)."""

    patient = serializers.IntegerField()
    message = serializers.CharField()


class MoodTrendPointSerializer(serializers.Serializer):
    entry_date = serializers.DateField()
    score = serializers.IntegerField(allow_null=True)
    energy_level = serializers.IntegerField(allow_null=True)
    sleep_hours = serializers.FloatField(allow_null=True)


class SymptomFrequencyItemSerializer(serializers.Serializer):
    symptom = serializers.CharField()
    count = serializers.IntegerField()
    average_severity = serializers.FloatField(allow_null=True)
