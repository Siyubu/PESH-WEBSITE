import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def new_offline_code():
    return f"PESH-ALL-{secrets.token_hex(4).upper()}"


class OfflineLearner(models.Model):
    """A learner registered in person (at the hub, no internet/device of their own) via the Android staff app."""

    client_id = models.UUIDField(unique=True, help_text="Generated on the phone. Lets a retried sync avoid creating a duplicate.")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    country = models.CharField("Country of origin", max_length=100)
    age = models.PositiveSmallIntegerField()
    grade = models.CharField(max_length=50, help_text="e.g. P5, S3")
    is_student = models.BooleanField(default=True)
    school = models.CharField(max_length=200, blank=True, help_text="Required when the learner is a student.")
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="offline_registrations")
    created_at = models.DateTimeField(default=timezone.now, help_text="When the signup was filled in on the phone (may be before it synced).")
    synced_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name()


class OfflineCertificate(models.Model):
    """A single certificate covering all courses, issued by an admin for an in-person learner."""

    learner = models.OneToOneField(OfflineLearner, on_delete=models.PROTECT, related_name="certificate")
    code = models.CharField(max_length=30, unique=True, default=new_offline_code)
    course_titles = models.JSONField(help_text="Snapshot of the course names at the time this was issued.")
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="issued_offline_certificates")
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code
