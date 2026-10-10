from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient
from django.test import TestCase

from .models import Course, Lesson

User = get_user_model()


def make_course(slug="demo", lessons=2):
    c = Course.objects.create(slug=slug, title="Demo Course", icon="x")
    for i in range(lessons):
        Lesson.objects.create(course=c, key=f"l{i+1}", order=i, title=f"Lesson {i+1}", blocks=[{"t": "p", "text": "hi"}])
    return c


class CourseApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.course = make_course()

    def test_catalog_and_lesson_are_public(self):
        r = self.client.get("/api/courses/")
        self.assertEqual(r.json()[0]["lesson_count"], 2)
        r = self.client.get("/api/courses/demo/lessons/l1/")
        self.assertEqual(r.json()["blocks"][0]["text"], "hi")

    def test_catalog_respects_course_order(self):
        Course.objects.filter(slug="demo").update(order=1)
        Course.objects.create(slug="a-late", title="A", order=5)
        Course.objects.create(slug="z-early", title="Z", order=0)
        self.assertEqual([c["slug"] for c in self.client.get("/api/courses/").json()], ["z-early", "demo", "a-late"])

    def test_progress_requires_login(self):
        self.assertEqual(self.client.post("/api/courses/demo/lessons/l1/complete/").status_code, 403)

    def test_mark_and_unmark_progress(self):
        user = User.objects.create_user("a@x.com", "pw-12345-x", full_name="A")
        self.client.force_authenticate(user)
        r = self.client.post("/api/courses/demo/lessons/l1/complete/")
        self.assertEqual(r.json()["completed"], ["l1"])
        self.client.post("/api/courses/demo/lessons/l1/complete/")  # idempotent
        r = self.client.post("/api/courses/demo/lessons/l2/complete/")
        self.assertEqual(r.json()["percent"], 100)
        r = self.client.delete("/api/courses/demo/lessons/l2/complete/")
        self.assertEqual(r.json()["percent"], 50)
        detail = self.client.get("/api/courses/demo/").json()
        self.assertEqual(detail["completed"], ["l1"])

    def test_unpublished_course_hidden(self):
        Course.objects.update(published=False)
        self.assertEqual(self.client.get("/api/courses/").json(), [])
        self.assertEqual(self.client.get("/api/courses/demo/").status_code, 404)


class ImportTests(TestCase):
    def test_import_is_idempotent_and_only_new_keeps_edits(self):
        call_command("import_courses", verbosity=0)
        self.assertEqual(Course.objects.count(), 4)
        lesson = Lesson.objects.filter(course__slug="excel").first()
        lesson.title = "Edited in admin"
        lesson.save()
        call_command("import_courses", "--only-new", verbosity=0)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, "Edited in admin")
        self.assertEqual(Lesson.objects.filter(course__slug="excel").count(), 8)
        call_command("import_courses", verbosity=0)
        lesson.refresh_from_db()
        self.assertNotEqual(lesson.title, "Edited in admin")
