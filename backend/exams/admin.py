from django.contrib import admin

from .models import Exam, ExamAttempt, Question


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 0
    fields = ("order", "text", "options", "correct_index", "active")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "pass_percent", "questions_per_attempt", "time_limit_minutes", "published")
    inlines = [QuestionInline]


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ("started_at", "user", "exam", "percent", "passed", "status")
    list_filter = ("passed", "status", "exam__course")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in ExamAttempt._meta.fields]

    def has_add_permission(self, request):
        return False
