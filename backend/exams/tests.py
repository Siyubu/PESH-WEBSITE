from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from courses.models import LessonProgress
from courses.tests import make_course

from .models import Exam, ExamAttempt, Question

User = get_user_model()


def make_exam(course, questions=6, per_attempt=4, pass_percent=75, wait=0, minutes=30):
    exam = Exam.objects.create(
        course=course, pass_percent=pass_percent, questions_per_attempt=per_attempt, retake_wait_minutes=wait, time_limit_minutes=minutes
    )
    for i in range(questions):
        Question.objects.create(exam=exam, order=i, text=f"Q{i}?", options=[f"right{i}", f"wrong{i}a", f"wrong{i}b"], correct_index=0)
    return exam


def pass_exam(user, exam):
    return ExamAttempt.objects.create(
        user=user, exam=exam, status=ExamAttempt.SUBMITTED, expires_at=timezone.now(), submitted_at=timezone.now(),
        correct_count=exam.questions_per_attempt, total=exam.questions_per_attempt, percent=100, passed=True,
    )


class ExamFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user("l@x.com", "Sup3r-secret!", full_name="Learner")
        self.client.force_authenticate(self.user)
        self.course = make_course("word", lessons=2)
        self.exam = make_exam(self.course)

    def finish_lessons(self):
        for l in self.course.lessons.all():
            LessonProgress.objects.create(user=self.user, lesson=l)

    def start(self):
        return self.client.post("/api/exams/word/start/")

    def answer_all(self, payload, right=True):
        """Answer every question right (or all wrong) by reading the shuffled options."""
        answers = {}
        for q in payload["questions"]:
            pick = next(i for i, o in enumerate(q["options"]) if o.startswith("right")) if right else next(i for i, o in enumerate(q["options"]) if not o.startswith("right"))
            answers[str(q["id"])] = pick
        return answers

    def test_requires_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/exams/word/").status_code, 403)

    def test_cannot_start_before_finishing_lessons(self):
        self.assertEqual(self.start().status_code, 403)
        self.assertFalse(self.client.get("/api/exams/word/").json()["lessons_complete"])

    def test_questions_never_include_answers(self):
        self.finish_lessons()
        r = self.start()
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(len(body["questions"]), 4)
        for q in body["questions"]:
            self.assertEqual(set(q), {"id", "text", "options"})
        self.assertNotIn("correct_index", r.content.decode())
        self.assertNotIn("explanation", r.content.decode())

    def test_pass_with_all_correct(self):
        self.finish_lessons()
        body = self.start().json()
        r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body)}, format="json").json()
        self.assertTrue(r["passed"])
        self.assertEqual(r["percent"], 100)
        self.assertTrue(all(item["correct"] for item in r["review"]))
        self.assertTrue(self.client.get("/api/exams/word/").json()["passed"])

    def test_fail_never_reveals_answers_and_can_retry_immediately_and_repeatedly(self):
        self.finish_lessons()
        for _ in range(4):  # as many attempts as the learner wants, no waiting
            body = self.start().json()
            r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body, right=False)}, format="json")
            data = r.json()
            self.assertFalse(data["passed"])
            self.assertEqual(data["percent"], 0)
            raw = r.content.decode()
            for leak in ("correct_index", "explanation", "options"):
                self.assertNotIn(leak, raw)
            for item in data["review"]:
                self.assertEqual(set(item), {"id", "text", "your_answer", "correct"})
                self.assertFalse(item["correct"])
                self.assertFalse(item["your_answer"].startswith("right"))
        self.assertEqual(ExamAttempt.objects.count(), 4)
        body = self.start().json()
        r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body)}, format="json").json()
        self.assertTrue(r["passed"])

    def test_optional_retake_wait_still_works_when_an_admin_sets_one(self):
        self.finish_lessons()
        self.exam.retake_wait_minutes = 15
        self.exam.save()
        body = self.start().json()
        self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body, right=False)}, format="json")
        retry = self.start()
        self.assertEqual(retry.status_code, 429)
        self.assertGreater(retry.json()["retry_in_seconds"], 0)
        ExamAttempt.objects.update(submitted_at=timezone.now() - timedelta(minutes=20))
        self.assertEqual(self.start().status_code, 201)

    def test_pass_mark_boundary(self):
        self.finish_lessons()
        body = self.start().json()
        answers = self.answer_all(body)
        first = str(body["questions"][0]["id"])
        answers[first] = next(i for i, o in enumerate(body["questions"][0]["options"]) if not o.startswith("right"))
        r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": answers}, format="json").json()
        self.assertEqual(r["percent"], 75)  # 3 of 4 with a 75% pass mark
        self.assertTrue(r["passed"])

    def test_blank_and_bogus_answers_score_zero(self):
        self.finish_lessons()
        body = self.start().json()
        r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": {str(body["questions"][0]["id"]): 99, "junk": 1}}, format="json").json()
        self.assertEqual(r["percent"], 0)

    def test_resume_and_double_submit(self):
        self.finish_lessons()
        first = self.start().json()
        again = self.start()
        self.assertEqual(again.json()["id"], first["id"])
        self.assertEqual([q["id"] for q in again.json()["questions"]], [q["id"] for q in first["questions"]])
        self.client.post(f"/api/exams/attempts/{first['id']}/submit/", {"answers": {}}, format="json")
        second = self.client.post(f"/api/exams/attempts/{first['id']}/submit/", {"answers": self.answer_all(first)}, format="json")
        self.assertEqual(second.status_code, 409)
        self.assertFalse(self.client.get("/api/exams/word/").json()["passed"])

    def test_late_submission_counts_as_failed(self):
        self.finish_lessons()
        body = self.start().json()
        ExamAttempt.objects.update(expires_at=timezone.now() - timedelta(minutes=5))
        r = self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body)}, format="json").json()
        self.assertFalse(r["passed"])
        self.assertEqual(r["status"], "expired")

    def test_cannot_see_or_submit_someone_elses_attempt(self):
        self.finish_lessons()
        body = self.start().json()
        other = User.objects.create_user("o@x.com", "Sup3r-secret!", full_name="Other")
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(f"/api/exams/attempts/{body['id']}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": {}}, format="json").status_code, 404)

    def test_resuming_via_attempt_endpoint_and_finished_view(self):
        self.finish_lessons()
        body = self.start().json()
        self.assertEqual(self.client.get(f"/api/exams/attempts/{body['id']}/").json()["state"], "in_progress")
        self.client.post(f"/api/exams/attempts/{body['id']}/submit/", {"answers": self.answer_all(body)}, format="json")
        self.assertEqual(self.client.get(f"/api/exams/attempts/{body['id']}/").json()["state"], "finished")

    def test_inactive_questions_are_not_used(self):
        self.finish_lessons()
        Question.objects.filter(exam=self.exam).exclude(order__lt=2).update(active=False)
        self.assertEqual(len(self.start().json()["questions"]), 2)


class ImportExamTests(TestCase):
    def test_bundled_banks_are_valid(self):
        call_command("import_courses", verbosity=0)
        call_command("import_exams", verbosity=0)
        self.assertEqual(Exam.objects.count(), 4)
        for exam in Exam.objects.all():
            qs = list(exam.questions.all())
            self.assertGreaterEqual(len(qs), 30, exam.course.slug)
            for q in qs:
                q.clean()
                self.assertEqual(len(set(q.options)), len(q.options), q.text)
            self.assertEqual(len({q.text for q in qs}), len(qs), "duplicate question text")

    def test_reimport_updates_in_place_and_keeps_attempt_history_readable(self):
        call_command("import_courses", verbosity=0)
        call_command("import_exams", verbosity=0)
        exam = Exam.objects.get(course__slug="word")
        q = exam.questions.first()
        ids = set(exam.questions.values_list("id", flat=True))
        q.options = ["changed", "in", "admin"]
        q.correct_index = 2
        q.save()
        Question.objects.create(exam=exam, order=99, text="A question no longer in the file", options=["a", "b"], correct_index=0)
        call_command("import_exams", verbosity=0)
        q.refresh_from_db()
        self.assertNotEqual(q.options, ["changed", "in", "admin"])  # restored from the file
        self.assertEqual(set(exam.questions.filter(active=True).values_list("id", flat=True)), ids)  # same rows, none duplicated
        self.assertFalse(exam.questions.get(text="A question no longer in the file").active)  # retired, not deleted

    def test_only_new_keeps_admin_edits(self):
        call_command("import_courses", verbosity=0)
        call_command("import_exams", verbosity=0)
        exam = Exam.objects.get(course__slug="word")
        exam.pass_percent = 90
        exam.save()
        exam.questions.first().delete()
        n = exam.questions.count()
        call_command("import_exams", "--only-new", verbosity=0)
        exam.refresh_from_db()
        self.assertEqual(exam.pass_percent, 90)
        self.assertEqual(exam.questions.count(), n)
