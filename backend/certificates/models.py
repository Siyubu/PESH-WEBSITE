import secrets
import uuid

from django.conf import settings
from django.db import models

from courses.models import Course


def new_code(course):
    return f"PESH-{course.slug.upper()[:4]}-{secrets.token_hex(4).upper()}"


class Payment(models.Model):
    PENDING, SUCCESSFUL, FAILED = "pending", "successful", "failed"
    STATUS_CHOICES = [(PENDING, "Pending"), (SUCCESSFUL, "Successful"), (FAILED, "Failed")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="payments")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    amount = models.PositiveIntegerField(help_text="Amount sent to MoMo (price is set by the server).")
    currency = models.CharField(max_length=3)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    phone_last4 = models.CharField(max_length=4, blank=True)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} {self.course.slug} {self.status}"


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="certificates")
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="certificate")
    code = models.CharField(max_length=30, unique=True)
    learner_name = models.CharField(max_length=150)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "course"], name="one_certificate_per_user_course")]

    def __str__(self):
        return self.code
