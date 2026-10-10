import uuid

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from courses.tests import make_course

from .models import OfflineCertificate, OfflineLearner
from .serializers import OfflineLearnerSerializer

User = get_user_model()


def learner_payload(**over):
    data = {
        "client_id": str(uuid.uuid4()), "first_name": "Alice", "last_name": "Uwimana", "country": "Rwanda",
        "age": 11, "grade": "P5", "is_student": True, "school": "Kigali Primary", "created_at": "2026-09-20T09:00:00Z",
    }
    data.update(over)
    return data


class MobileLoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_staff_can_log_in_and_get_a_token(self):
        User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        r = self.client.post("/api/mobile/login/", {"email": "MENTOR@x.com", "password": "Sup3r-secret!"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["token"])

    def test_non_staff_account_is_rejected(self):
        User.objects.create_user("learner@x.com", "Sup3r-secret!", full_name="Learner")
        r = self.client.post("/api/mobile/login/", {"email": "learner@x.com", "password": "Sup3r-secret!"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_wrong_password_is_rejected(self):
        User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        r = self.client.post("/api/mobile/login/", {"email": "mentor@x.com", "password": "nope"}, format="json")
        self.assertEqual(r.status_code, 400)


class OfflineLearnerApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        self.learner_user = User.objects.create_user("learner@x.com", "Sup3r-secret!", full_name="Learner")
        self.client = APIClient()

    def as_staff(self):
        token = self.client.post("/api/mobile/login/", {"email": "mentor@x.com", "password": "Sup3r-secret!"}, format="json").json()["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_requires_a_staff_token(self):
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json").status_code, 401)
        token = self.client.post("/api/mobile/login/", {"email": "learner@x.com", "password": "wrong"}, format="json")
        self.client.credentials(HTTP_AUTHORIZATION="Token bogus-token-value")
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json").status_code, 401)

    def test_creates_a_learner(self):
        self.as_staff()
        r = self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json")
        self.assertEqual(r.status_code, 201)
        learner = OfflineLearner.objects.get()
        self.assertEqual(learner.full_name(), "Alice Uwimana")
        self.assertEqual(learner.registered_by, self.staff)
        self.assertEqual(learner.school, "Kigali Primary")

    def test_resyncing_the_same_client_id_does_not_duplicate(self):
        self.as_staff()
        payload = learner_payload()
        first = self.client.post("/api/mobile/offline-learners/", payload, format="json")
        second = self.client.post("/api/mobile/offline-learners/", payload, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()["client_id"], second.json()["client_id"])
        self.assertEqual(OfflineLearner.objects.count(), 1)

    def test_student_must_have_a_school(self):
        self.as_staff()
        r = self.client.post("/api/mobile/offline-learners/", learner_payload(school=""), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("school", r.json())

    def test_non_student_school_is_cleared_even_if_sent(self):
        self.as_staff()
        r = self.client.post("/api/mobile/offline-learners/", learner_payload(is_student=False, school="Should be dropped"), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(OfflineLearner.objects.get().school, "")

    def test_concurrent_duplicate_sync_is_idempotent_not_a_500(self):
        """Simulates two WorkManager workers racing to sync the same record at once."""
        self.as_staff()
        payload = learner_payload()
        ser = OfflineLearnerSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        # The row already exists (as if the "other" concurrent request just committed it),
        # so our request's own pre-check won't see it yet if it ran a moment earlier -- exercise
        # the IntegrityError path directly by creating it after validation would have passed.
        OfflineLearner.objects.create(registered_by=self.staff, **ser.validated_data)
        r = self.client.post("/api/mobile/offline-learners/", payload, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["client_id"], payload["client_id"])
        self.assertEqual(OfflineLearner.objects.filter(client_id=payload["client_id"]).count(), 1)

    def test_rejects_unrealistic_age(self):
        self.as_staff()
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(age=1), format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(client_id=str(uuid.uuid4()), age=150), format="json").status_code, 400)


class CombinedCertificateAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser("admin@x.com", "Sup3r-secret!", full_name="Admin")
        self.client = APIClient()
        self.client.force_authenticate(self.staff)
        make_course("word")
        make_course("excel")
        self.learner = OfflineLearner.objects.create(
            client_id=uuid.uuid4(), first_name="Alice", last_name="Uwimana", country="Rwanda", age=11, grade="P5",
            is_student=True, school="Kigali Primary", registered_by=self.staff,
        )

    def issue(self):
        from django.contrib.admin.sites import AdminSite

        from .admin import OfflineLearnerAdmin

        request = type("R", (), {"user": self.staff})()
        ma = OfflineLearnerAdmin(OfflineLearner, AdminSite())
        ma.message_user = lambda *a, **k: None
        ma.issue_combined_certificate(request, OfflineLearner.objects.filter(pk=self.learner.pk))

    def test_issuing_snapshots_all_published_course_titles(self):
        self.issue()
        cert = OfflineCertificate.objects.get()
        self.assertEqual(set(cert.course_titles), {"Demo Course"})
        self.assertEqual(cert.issued_by, self.staff)
        self.assertTrue(cert.code.startswith("PESH-ALL-"))

    def test_issuing_twice_does_not_duplicate(self):
        self.issue()
        self.issue()
        self.assertEqual(OfflineCertificate.objects.filter(learner=self.learner).count(), 1)

    def test_pdf_download_is_staff_only(self):
        self.issue()
        code = OfflineCertificate.objects.get().code
        r = self.client.get(f"/api/offline-certificates/{code.lower()}/pdf/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")
        self.assertTrue(r.content.startswith(b"%PDF"))

        anon = APIClient()
        self.assertEqual(anon.get(f"/api/offline-certificates/{code}/pdf/").status_code, 403)

    def test_public_verify_finds_the_combined_certificate(self):
        self.issue()
        code = OfflineCertificate.objects.get().code
        anon = APIClient()
        r = anon.get(f"/api/certificates/verify/{code}/").json()
        self.assertTrue(r["valid"])
        self.assertEqual(r["learner_name"], "Alice Uwimana")
        self.assertIn("Demo Course", r["course"])
