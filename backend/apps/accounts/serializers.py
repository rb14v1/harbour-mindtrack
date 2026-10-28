from zoneinfo import ZoneInfoNotFoundError, available_timezones

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import PatientProfile, TherapistProfile, User

_VALID_TIMEZONES = available_timezones()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = ["id", "role", "date_joined"]


class PatientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            "id", "user", "email", "first_name", "last_name",
            "timezone", "date_of_birth", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_timezone(self, value):
        if value not in _VALID_TIMEZONES:
            raise serializers.ValidationError("Not a recognised IANA timezone name.")
        return value


class TherapistProfileSerializer(serializers.ModelSerializer):
    """Full serializer - used for the therapist's own profile view/edit."""

    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = TherapistProfile
        fields = [
            "id", "user", "email", "first_name", "last_name",
            "license_number", "bio", "specialties", "years_experience",
            "accepting_new_patients", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class TherapistDirectorySerializer(serializers.ModelSerializer):
    """Public directory listing shown to patients browsing for a therapist.

    Deliberately excludes license_number (administrative detail) and never
    includes any patient data - directory rows are therapist-only fields.
    """

    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = TherapistProfile
        fields = [
            "id", "user", "email", "first_name", "last_name",
            "bio", "specialties", "years_experience", "accepting_new_patients",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Role-aware self-registration.

    Both patients and therapists may self-register (unlike the sibling
    appointment-hub app, MindTrack has no front-desk/admin provisioning
    concept) - the role choice drives which profile row is created.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.ChoiceField(choices=User.Role.choices)
    timezone = serializers.CharField(write_only=True, required=False, default="UTC")

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "role", "timezone"]

    def validate_timezone(self, value):
        if value not in _VALID_TIMEZONES:
            raise serializers.ValidationError("Not a recognised IANA timezone name.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        timezone_name = validated_data.pop("timezone", "UTC")
        role = validated_data["role"]

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if role == User.Role.PATIENT:
            PatientProfile.objects.create(user=user, timezone=timezone_name)
        else:
            TherapistProfile.objects.create(user=user)

        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds `role` to the JWT claims.

    The claim is a convenience for the frontend only - every request is
    re-validated server-side against the live User.role in the database
    (see common/permissions-style checks across the apps), so a stale or
    tampered claim can never grant access beyond what the DB currently
    allows.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token
