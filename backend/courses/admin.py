from django.contrib import admin

from .models import Course, Lesson, LessonProgress


class LessonInline(admin.TabularInline):
    model = Lesson
    fields = ("key", "order", "title")
    extra = 0
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order", "published")
    list_editable = ("order", "published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "key", "order")
    list_filter = ("course",)
    search_fields = ("title",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed_at")
    list_filter = ("lesson__course",)
    raw_id_fields = ("user", "lesson")
