from .models import Course, LessonProgress


def completed_keys(user, course):
    if not user.is_authenticated:
        return []
    return list(
        LessonProgress.objects.filter(user=user, lesson__course=course)
        .order_by("lesson__order")
        .values_list("lesson__key", flat=True)
    )


def is_course_complete(user, course):
    total = course.lessons.count()
    return total > 0 and LessonProgress.objects.filter(user=user, lesson__course=course).count() >= total


def published_courses():
    return Course.objects.filter(published=True)
