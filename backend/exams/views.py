from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from courses.services import is_course_complete, published_courses

from . import services
from .models import Exam, ExamAttempt


def get_exam(slug):
    course = get_object_or_404(published_courses(), slug=slug)
    return get_object_or_404(Exam, course=course, published=True)


def secs_left(attempt):
    return max(0, int((attempt.expires_at - timezone.now()).total_seconds()))


def attempt_payload(attempt):
    return {
        "id": attempt.id,
        "seconds_left": secs_left(attempt),
        "time_limit_minutes": attempt.exam.time_limit_minutes,
        "questions": services.attempt_questions(attempt),
    }


class ExamInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        exam = get_exam(slug)
        services.close_expired(request.user, exam)
        attempts = ExamAttempt.objects.filter(user=request.user, exam=exam, submitted_at__isnull=False)
        best = attempts.order_by("-percent").first()
        current = services.in_progress_attempt(request.user, exam)
        wait_until = services.next_attempt_at(request.user, exam)
        return Response(
            {
                "course": {"slug": exam.course.slug, "title": exam.course.title},
                "title": exam.title,
                "pass_percent": exam.pass_percent,
                "question_count": min(exam.questions_per_attempt, exam.questions.filter(active=True).count()),
                "time_limit_minutes": exam.time_limit_minutes,
                "retake_wait_minutes": exam.retake_wait_minutes,
                "lessons_complete": is_course_complete(request.user, exam.course),
                "passed": services.has_passed(request.user, exam.course),
                "best_percent": best.percent if best else None,
                "attempts": attempts.count(),
                "in_progress_attempt": current.id if current else None,
                "retry_in_seconds": max(0, int((wait_until - timezone.now()).total_seconds())) if wait_until else 0,
            }
        )


class StartView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "exam"

    def post(self, request, slug):
        exam = get_exam(slug)
        try:
            attempt = services.start_attempt(request.user, exam)
        except services.ExamError as e:
            body = {"error": str(e)}
            if e.status == 429:
                wait = services.next_attempt_at(request.user, exam)
                body["retry_in_seconds"] = max(0, int((wait - timezone.now()).total_seconds())) if wait else 0
            return Response(body, status=e.status)
        return Response(attempt_payload(attempt), status=201)


class AttemptView(APIView):
    """Resume an in-progress attempt, or read the result of a finished one."""

    permission_classes = [IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt.objects.select_related("exam__course"), pk=attempt_id, user=request.user)
        if attempt.status == ExamAttempt.IN_PROGRESS and secs_left(attempt) > 0:
            return Response({"state": "in_progress", **attempt_payload(attempt)})
        if attempt.status == ExamAttempt.IN_PROGRESS:
            services.close_expired(request.user, attempt.exam)
            attempt.refresh_from_db()
        return Response({"state": "finished", **services.attempt_result(attempt)})


class SubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, attempt_id):
        get_object_or_404(ExamAttempt, pk=attempt_id, user=request.user)
        answers = request.data.get("answers") if isinstance(request.data, dict) else None
        try:
            attempt = services.submit_attempt(attempt_id, request.user, answers if isinstance(answers, dict) else {})
        except services.ExamError as e:
            return Response({"error": str(e)}, status=e.status)
        attempt = ExamAttempt.objects.select_related("exam").get(pk=attempt.pk)
        return Response(services.attempt_result(attempt))
