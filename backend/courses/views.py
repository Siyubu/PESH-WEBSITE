from django.conf import settings
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Lesson, LessonProgress
from .services import completed_keys, published_courses


def exam_passed(user, course):
    if not user.is_authenticated:
        return False
    from exams.services import has_passed

    return has_passed(user, course)


def course_summary(course, user, lesson_count=None):
    lesson_count = course.lessons.count() if lesson_count is None else lesson_count
    done = len(completed_keys(user, course))
    return {
        "slug": course.slug,
        "title": course.title,
        "icon": course.icon,
        "level": course.level,
        "description": course.description,
        "certificate_price": settings.CERTIFICATE_PRICE,
        "lesson_count": lesson_count,
        "completed_count": done,
        "percent": round(100 * done / lesson_count) if lesson_count else 0,
        "has_exam": hasattr(course, "exam") and course.exam.published,
        "exam_passed": exam_passed(user, course),
    }


class CourseListView(APIView):
    def get(self, request):
        courses = published_courses().annotate(n=Count("lessons")).order_by("order", "title")
        return Response([course_summary(c, request.user, c.n) for c in courses])


class CourseDetailView(APIView):
    def get(self, request, slug):
        course = get_object_or_404(published_courses(), slug=slug)
        data = course_summary(course, request.user)
        data["lessons"] = [
            {"key": l.key, "title": l.title, "summary": l.summary} for l in course.lessons.all()
        ]
        data["completed"] = completed_keys(request.user, course)
        return Response(data)


class LessonDetailView(APIView):
    def get(self, request, slug, key):
        lesson = get_object_or_404(Lesson, course__slug=slug, course__published=True, key=key)
        return Response(
            {"key": lesson.key, "title": lesson.title, "summary": lesson.summary, "goals": lesson.goals, "blocks": lesson.blocks}
        )


class LessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def _response(self, request, lesson):
        done = completed_keys(request.user, lesson.course)
        total = lesson.course.lessons.count()
        return Response({"completed": done, "percent": round(100 * len(done) / total) if total else 0})

    def post(self, request, slug, key):
        lesson = get_object_or_404(Lesson, course__slug=slug, course__published=True, key=key)
        try:
            LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        except IntegrityError:
            pass  # double-click race: already recorded
        return self._response(request, lesson)

    def delete(self, request, slug, key):
        lesson = get_object_or_404(Lesson, course__slug=slug, course__published=True, key=key)
        LessonProgress.objects.filter(user=request.user, lesson=lesson).delete()
        return self._response(request, lesson)
