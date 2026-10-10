import random
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from courses.services import is_course_complete

from .models import Exam, ExamAttempt, Question

SUBMIT_GRACE = timedelta(seconds=60)


class ExamError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def has_passed(user, course):
    return ExamAttempt.objects.filter(user=user, exam__course=course, passed=True).exists()


def close_expired(user, exam):
    """Unsubmitted attempts past their deadline count as failed."""
    now = timezone.now()
    for a in ExamAttempt.objects.filter(user=user, exam=exam, status=ExamAttempt.IN_PROGRESS, expires_at__lt=now - SUBMIT_GRACE):
        a.status = ExamAttempt.EXPIRED
        a.submitted_at = a.expires_at
        a.save(update_fields=["status", "submitted_at"])


def next_attempt_at(user, exam):
    """When the learner may try again after their latest failed attempt (None if they can start now)."""
    last = (
        ExamAttempt.objects.filter(user=user, exam=exam, submitted_at__isnull=False, passed=False)
        .order_by("-submitted_at")
        .first()
    )
    if not last:
        return None
    at = last.submitted_at + timedelta(minutes=exam.retake_wait_minutes)
    return at if at > timezone.now() else None


def in_progress_attempt(user, exam):
    return ExamAttempt.objects.filter(user=user, exam=exam, status=ExamAttempt.IN_PROGRESS, expires_at__gt=timezone.now()).first()


def start_attempt(user, exam):
    if not is_course_complete(user, exam.course):
        raise ExamError("Finish all lessons before taking the exam.", 403)
    close_expired(user, exam)
    existing = in_progress_attempt(user, exam)
    if existing:
        return existing
    wait_until = next_attempt_at(user, exam)
    if wait_until:
        raise ExamError("Please review the lessons and try again a little later.", 429)
    bank = list(exam.questions.filter(active=True))
    if not bank:
        raise ExamError("This exam has no questions yet.", 503)
    picked = random.sample(bank, min(exam.questions_per_attempt, len(bank)))
    layout = []
    for q in picked:
        order = list(range(len(q.options)))
        random.shuffle(order)
        layout.append({"q": q.id, "order": order})
    return ExamAttempt.objects.create(
        user=user,
        exam=exam,
        layout=layout,
        total=len(layout),
        expires_at=timezone.now() + timedelta(minutes=exam.time_limit_minutes),
    )


def attempt_questions(attempt):
    """Questions as shown to the learner: shuffled options, no answers."""
    by_id = {q.id: q for q in Question.objects.filter(pk__in=[l["q"] for l in attempt.layout])}
    return [
        {"id": l["q"], "text": by_id[l["q"]].text, "options": [by_id[l["q"]].options[i] for i in l["order"]]}
        for l in attempt.layout
    ]


@transaction.atomic
def submit_attempt(attempt_id, user, answers):
    attempt = ExamAttempt.objects.select_for_update().select_related("exam").get(pk=attempt_id, user=user)
    if attempt.status != ExamAttempt.IN_PROGRESS:
        raise ExamError("This attempt was already submitted.", 409)
    now = timezone.now()
    attempt.submitted_at = now
    if now > attempt.expires_at + SUBMIT_GRACE:
        attempt.status = ExamAttempt.EXPIRED
        attempt.submitted_at = attempt.expires_at
        attempt.save()
        return attempt

    clean = {}
    correct = 0
    by_id = {q.id: q for q in Question.objects.filter(pk__in=[l["q"] for l in attempt.layout])}
    for l in attempt.layout:
        raw = (answers or {}).get(str(l["q"]))
        if isinstance(raw, int) and not isinstance(raw, bool) and 0 <= raw < len(l["order"]):
            clean[str(l["q"])] = raw
            if l["order"][raw] == by_id[l["q"]].correct_index:
                correct += 1
    attempt.answers = clean
    attempt.status = ExamAttempt.SUBMITTED
    attempt.correct_count = correct
    attempt.total = len(attempt.layout)
    attempt.percent = round(100 * correct / attempt.total) if attempt.total else 0
    attempt.passed = attempt.percent >= attempt.exam.pass_percent
    attempt.save()
    return attempt


def attempt_result(attempt):
    """Review shown after submitting. Shows which questions were missed, never the right answers."""
    by_id = {q.id: q for q in Question.objects.filter(pk__in=[l["q"] for l in attempt.layout])}
    review = []
    for l in attempt.layout:
        q = by_id[l["q"]]
        sel = attempt.answers.get(str(l["q"]))
        ok = sel is not None and l["order"][sel] == q.correct_index
        yours = q.options[l["order"][sel]] if sel is not None else None
        review.append({"id": q.id, "text": q.text, "your_answer": yours, "correct": ok})
    return {
        "id": attempt.id,
        "status": attempt.status,
        "passed": attempt.passed,
        "percent": attempt.percent,
        "correct_count": attempt.correct_count,
        "total": attempt.total,
        "pass_percent": attempt.exam.pass_percent,
        "review": review,
    }
