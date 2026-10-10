from rest_framework import serializers

from .models import OfflineLearner

MIN_AGE, MAX_AGE = 3, 100


class OfflineLearnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineLearner
        fields = ["client_id", "first_name", "last_name", "country", "age", "grade", "is_student", "school", "created_at"]
        extra_kwargs = {"created_at": {"required": False}}

    def validate_age(self, value):
        if not MIN_AGE <= value <= MAX_AGE:
            raise serializers.ValidationError("Enter a realistic age.")
        return value

    def validate(self, attrs):
        if attrs.get("is_student", True) and not attrs.get("school", "").strip():
            raise serializers.ValidationError({"school": "School is required for students."})
        if not attrs.get("is_student", True):
            attrs["school"] = ""
        return attrs
