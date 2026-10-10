from django.conf import settings
from django.db import models


class Course(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)
    icon = models.CharField(max_length=8, blank=True)
    level = models.CharField(max_length=40, default="Beginner")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """`key` (l1, l2, ...) is stable so learner progress survives content edits."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    key = models.CharField(max_length=20)
    order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300, blank=True)
    goals = models.JSONField(default=list, blank=True)
    blocks = models.JSONField(default=list, blank=True, help_text="Ordered content blocks (headings, paragraphs, lists, tables).")

    class Meta:
        ordering = ["course", "order"]
        constraints = [models.UniqueConstraint(fields=["course", "key"], name="unique_lesson_key_per_course")]

    def __str__(self):
        return f"{self.course.slug}/{self.key}: {self.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "lesson"], name="unique_progress_per_lesson")]

    def __str__(self):
        return f"{self.user_id} completed {self.lesson_id}"
