from datetime import date

from django.utils import timezone
from rest_framework import serializers

from .models import OfflineLearner

MIN_AGE, MAX_AGE = 3, 100


def age_on(dob, today):
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class OfflineLearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineLearner
        fields = [
            "client_id", "first_name", "last_name", "country", "date_of_birth", "is_student", "grade", "school",
            "created_at", "client_updated_at",
        ]
        extra_kwargs = {
            "created_at": {"required": False},
            "client_updated_at": {"required": False},
            "grade": {"required": False, "allow_blank": True},
            "school": {"required": False, "allow_blank": True},
        }

    def validate_date_of_birth(self, value):
        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        if not MIN_AGE <= age_on(value, today) <= MAX_AGE:
            raise serializers.ValidationError(f"Enter a realistic date of birth (age {MIN_AGE}-{MAX_AGE}).")
        return value

    def validate(self, attrs):
        if attrs.get("is_student", True):
            errors = {}
            if not attrs.get("grade", "").strip():
                errors["grade"] = "Grade is required for students."
            if not attrs.get("school", "").strip():
                errors["school"] = "School is required for students."
            if errors:
                raise serializers.ValidationError(errors)
        else:
            attrs["grade"] = ""
            attrs["school"] = ""
        return attrs
