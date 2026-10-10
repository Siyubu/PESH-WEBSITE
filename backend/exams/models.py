from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from courses.models import Course


class Exam(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="exam")
    title = models.CharField(max_length=150, default="Final exam")
    pass_percent = models.PositiveSmallIntegerField(default=70, validators=[MinValueValidator(1), MaxValueValidator(100)])
    questions_per_attempt = models.PositiveSmallIntegerField(default=20, help_text="Random questions drawn from the bank for each attempt.")
    time_limit_minutes = models.PositiveSmallIntegerField(default=30)
    retake_wait_minutes = models.PositiveSmallIntegerField(default=0, help_text="Minutes to wait after a failed attempt. 0 = retake immediately, as many times as needed.")
    published = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.course.title}: {self.title}"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveIntegerField(default=0)
    text = models.TextField()
    options = models.JSONField(help_text='List of 2-6 answer choices, e.g. ["Ctrl + C", "Ctrl + V"].')
    correct_index = models.PositiveSmallIntegerField(help_text="Position of the right answer in options, starting at 0.")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:80]

    def clean(self):
        from django.core.exceptions import ValidationError

        if not isinstance(self.options, list) or not 2 <= len(self.options) <= 6:
            raise ValidationError("Options must be a list of 2 to 6 choices.")
        if not 0 <= self.correct_index < len(self.options):
            raise ValidationError("correct_index must point at one of the options.")


class ExamAttempt(models.Model):
    IN_PROGRESS, SUBMITTED, EXPIRED = "in_progress", "submitted", "expired"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=12, default=IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    # [{"q": question_id, "order": [original option indexes in the order shown]}]
    layout = models.JSONField(default=list)
    answers = models.JSONField(default=dict, blank=True)
    correct_count = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    percent = models.PositiveSmallIntegerField(default=0)
    passed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user_id} {self.exam.course.slug} {self.percent}% {'passed' if self.passed else self.status}"
