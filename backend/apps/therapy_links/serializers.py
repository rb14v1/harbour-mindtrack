from rest_framework import serializers

from apps.accounts.models import User
from apps.therapy_links.models import PatientTherapistLink


class PatientTherapistLinkSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    patient_name = serializers.SerializerMethodField()
    therapist_email = serializers.EmailField(source="therapist.email", read_only=True)
    therapist_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientTherapistLink
        fields = [
            "id", "patient", "patient_email", "patient_name",
            "therapist", "therapist_email", "therapist_name",
            "status", "requested_by", "created_at", "responded_at",
            "ended_at", "end_reason",
        ]
        read_only_fields = [
            "id", "status", "requested_by", "created_at", "responded_at", "ended_at",
        ]

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}".strip() or obj.patient.email

    def get_therapist_name(self, obj):
        return f"{obj.therapist.first_name} {obj.therapist.last_name}".strip() or obj.therapist.email


class CreateLinkSerializer(serializers.Serializer):
    """Either a patient supplies `therapist` or a therapist supplies
    `patient` - whichever role the requester has determines which field is
    required."""

    patient = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Role.PATIENT), required=False)
    therapist = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role=User.Role.THERAPIST), required=False)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if user.is_patient:
            if "therapist" not in attrs:
                raise serializers.ValidationError("therapist is required.")
            attrs["patient"] = user
        elif user.is_therapist:
            if "patient" not in attrs:
                raise serializers.ValidationError("patient is required.")
            attrs["therapist"] = user
        else:
            raise serializers.ValidationError("Unrecognised role.")
        return attrs


class EndLinkSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, default="")
