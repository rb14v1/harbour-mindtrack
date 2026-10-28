from rest_framework import serializers

from apps.therapy_links.models import PatientTherapistLink
from apps.therapy_links.permissions import is_linked
from apps.therapy_notes.models import SessionNote


class SessionNoteSerializer(serializers.ModelSerializer):
    therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = SessionNote
        fields = [
            "id", "patient", "therapist", "therapist_name", "link",
            "session_date", "note_text", "visible_to_patient",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "therapist", "link", "created_at", "updated_at"]

    def get_therapist_name(self, obj):
        return f"{obj.therapist.first_name} {obj.therapist.last_name}".strip() or obj.therapist.email

    def validate_patient(self, value):
        request = self.context["request"]
        if not is_linked(request.user, value):
            raise serializers.ValidationError(
                "You do not have an active therapy link with this patient."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        link = PatientTherapistLink.objects.filter(
            patient=validated_data["patient"],
            therapist=request.user,
            status=PatientTherapistLink.Status.ACTIVE,
        ).first()
        validated_data["therapist"] = request.user
        validated_data["link"] = link
        return super().create(validated_data)


class PatientSessionNoteSerializer(serializers.ModelSerializer):
    """What a patient is allowed to see - note_text + visible_to_patient are
    the only fields shown, and the view's queryset already guarantees
    visible_to_patient=True for every row that reaches this serializer."""

    therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = SessionNote
        fields = ["id", "therapist", "therapist_name", "session_date", "note_text", "created_at"]
        read_only_fields = fields

    def get_therapist_name(self, obj):
        return f"{obj.therapist.first_name} {obj.therapist.last_name}".strip() or obj.therapist.email
