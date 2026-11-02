import uuid
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from courses.tests import make_course

from .models import OfflineCertificate, OfflineLearner
from .serializers import OfflineLearnerSerializer

User = get_user_model()


def years_ago(years, extra_days=10):
    return (timezone.localdate() - timedelta(days=365 * years + extra_days)).isoformat()


def learner_payload(**over):
    data = {
        "client_id": str(uuid.uuid4()), "first_name": "Alice", "last_name": "Uwimana", "country": "Rwanda",
        "date_of_birth": years_ago(11), "is_student": True, "grade": "P5", "school": "Kigali Primary",
        "created_at": "2026-09-20T09:00:00Z", "client_updated_at": "2026-09-20T09:00:00Z",
    }
    data.update(over)
    return data


class MobileLoginTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def login(self, email="mentor@x.com", password="Sup3r-secret!"):
        return self.client.post("/api/mobile/login/", {"email": email, "password": password}, format="json")

    def test_staff_can_log_in_and_get_a_token(self):
        User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        r = self.login("MENTOR@x.com")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["token"])

    def test_non_staff_account_is_rejected(self):
        User.objects.create_user("learner@x.com", "Sup3r-secret!", full_name="Learner")
        self.assertEqual(self.login("learner@x.com").status_code, 400)

    def test_wrong_password_is_rejected(self):
        User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        self.assertEqual(self.login(password="nope").status_code, 400)

    def test_each_login_issues_a_new_token_and_retires_the_old_one(self):
        User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        first = self.login().json()["token"]
        second = self.login().json()["token"]
        self.assertNotEqual(first, second)
        self.assertEqual(Token.objects.count(), 1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {first}")
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json").status_code, 401)


class TokenAndSessionLifetimeTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        self.client = APIClient()

    def test_limit_is_at_most_24_hours_and_cannot_be_raised(self):
        from django.conf import settings

        self.assertLessEqual(settings.AUTH_TOKEN_MAX_AGE_SECONDS, 24 * 60 * 60)
        self.assertEqual(settings.SESSION_COOKIE_AGE, settings.AUTH_TOKEN_MAX_AGE_SECONDS)
        self.assertFalse(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_token_works_inside_24h_and_is_rejected_after(self):
        token = Token.objects.create(user=self.staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        Token.objects.update(created=timezone.now() - timedelta(hours=23, minutes=59))
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json").status_code, 201)
        Token.objects.update(created=timezone.now() - timedelta(hours=24, minutes=1))
        r = self.client.post("/api/mobile/offline-learners/", learner_payload(), format="json")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(Token.objects.count(), 0)  # the expired token is deleted

    def test_web_session_expires_after_at_most_24_hours(self):
        self.client.force_login(self.staff)
        self.assertLessEqual(self.client.session.get_expiry_age(), 24 * 60 * 60)
        Session.objects.update(expire_date=timezone.now() - timedelta(seconds=1))
        self.assertIsNone(APIClient().get("/api/auth/session/").json()["user"])
        self.client.cookies.clear()


class OfflineLearnerApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user("mentor@x.com", "Sup3r-secret!", full_name="Mentor", is_staff=True)
        self.client = APIClient()

    def as_staff(self):
        token = self.client.post("/api/mobile/login/", {"email": "mentor@x.com", "password": "Sup3r-secret!"}, format="json").json()["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def post(self, **over):
        return self.client.post("/api/mobile/offline-learners/", learner_payload(**over), format="json")

    def test_requires_a_staff_token(self):
        self.assertEqual(self.post().status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION="Token bogus-token-value")
        self.assertEqual(self.post().status_code, 401)

    def test_creates_a_learner(self):
        self.as_staff()
        self.assertEqual(self.post().status_code, 201)
        learner = OfflineLearner.objects.get()
        self.assertEqual(learner.full_name(), "Alice Uwimana")
        self.assertEqual(learner.registered_by, self.staff)
        self.assertEqual((learner.grade, learner.school), ("P5", "Kigali Primary"))
        self.assertEqual(learner.age, 11)

    def test_invalid_client_id_is_a_400_not_a_500(self):
        self.as_staff()
        self.assertEqual(self.post(client_id="not-a-uuid").status_code, 400)
        r = self.client.post("/api/mobile/offline-learners/", {"first_name": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_resyncing_the_same_version_does_not_duplicate_or_change_anything(self):
        self.as_staff()
        payload = learner_payload()
        first = self.client.post("/api/mobile/offline-learners/", payload, format="json")
        second = self.client.post("/api/mobile/offline-learners/", payload, format="json")
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(OfflineLearner.objects.count(), 1)

    def test_student_needs_grade_and_school(self):
        self.as_staff()
        for missing in ("grade", "school"):
            r = self.post(**{missing: ""})
            self.assertEqual(r.status_code, 400)
            self.assertIn(missing, r.json())

    def test_non_student_grade_and_school_are_cleared_even_if_sent(self):
        self.as_staff()
        self.assertEqual(self.post(is_student=False, grade="P5", school="Dropped").status_code, 201)
        learner = OfflineLearner.objects.get()
        self.assertEqual((learner.grade, learner.school), ("", ""))

    def test_non_student_can_omit_grade_and_school(self):
        self.as_staff()
        payload = learner_payload(is_student=False)
        del payload["grade"], payload["school"]
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", payload, format="json").status_code, 201)

    def test_date_of_birth_rules(self):
        self.as_staff()
        self.assertEqual(self.post(date_of_birth=(timezone.localdate() + timedelta(days=1)).isoformat()).status_code, 400)
        self.assertEqual(self.post(date_of_birth=years_ago(1)).status_code, 400)  # too young
        self.assertEqual(self.post(date_of_birth=years_ago(150)).status_code, 400)  # too old
        self.assertEqual(self.post(date_of_birth="not-a-date").status_code, 400)
        self.assertEqual(self.post(date_of_birth=years_ago(3, extra_days=5)).status_code, 201)

    def test_age_is_computed_from_date_of_birth(self):
        today = timezone.localdate()
        learner = OfflineLearner(date_of_birth=date(today.year - 10, today.month, today.day))
        self.assertEqual(learner.age, 10)
        tomorrow = today + timedelta(days=1)
        learner.date_of_birth = date(tomorrow.year - 10, tomorrow.month, tomorrow.day)
        self.assertEqual(learner.age, 9)  # birthday not reached yet

    def test_edit_updates_the_existing_record(self):
        self.as_staff()
        original = learner_payload()
        self.client.post("/api/mobile/offline-learners/", original, format="json")
        fixed = {**original, "first_name": "Alicia", "grade": "P6", "country": "Uganda", "client_updated_at": "2026-09-21T10:00:00Z"}
        r = self.client.post("/api/mobile/offline-learners/", fixed, format="json")
        self.assertEqual(r.status_code, 200)
        learner = OfflineLearner.objects.get()
        self.assertEqual((learner.first_name, learner.grade, learner.country), ("Alicia", "P6", "Uganda"))
        self.assertEqual(learner.registered_by, self.staff)
        self.assertEqual(learner.created_at.isoformat(), "2026-09-20T09:00:00+00:00")  # an edit never rewrites created_at

    def test_a_late_arriving_older_version_does_not_undo_a_newer_edit(self):
        self.as_staff()
        v1 = learner_payload()
        v2 = {**v1, "first_name": "Alicia", "client_updated_at": "2026-09-21T10:00:00Z"}
        self.client.post("/api/mobile/offline-learners/", v1, format="json")
        self.client.post("/api/mobile/offline-learners/", v2, format="json")
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", v1, format="json").status_code, 200)
        self.assertEqual(OfflineLearner.objects.get().first_name, "Alicia")

    def test_edit_that_breaks_the_rules_is_rejected_and_changes_nothing(self):
        self.as_staff()
        original = learner_payload()
        self.client.post("/api/mobile/offline-learners/", original, format="json")
        bad = {**original, "grade": "", "client_updated_at": "2026-09-21T10:00:00Z"}
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", bad, format="json").status_code, 400)
        self.assertEqual(OfflineLearner.objects.get().grade, "P5")

    def test_edit_can_switch_a_student_to_non_student(self):
        self.as_staff()
        original = learner_payload()
        self.client.post("/api/mobile/offline-learners/", original, format="json")
        fixed = {**original, "is_student": False, "client_updated_at": "2026-09-21T10:00:00Z"}
        self.assertEqual(self.client.post("/api/mobile/offline-learners/", fixed, format="json").status_code, 200)
        learner = OfflineLearner.objects.get()
        self.assertEqual((learner.is_student, learner.grade, learner.school), (False, "", ""))

    def test_concurrent_duplicate_create_falls_back_to_an_update_not_a_500(self):
        """Two sync workers racing: the row appears between our check and our insert."""
        self.as_staff()
        payload = learner_payload()
        ser = OfflineLearnerSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        OfflineLearner.objects.create(registered_by=self.staff, **ser.validated_data)
        newer = {**payload, "first_name": "Alicia", "client_updated_at": "2026-09-22T10:00:00Z"}
        r = self.client.post("/api/mobile/offline-learners/", newer, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(OfflineLearner.objects.filter(client_id=payload["client_id"]).count(), 1)
        self.assertEqual(OfflineLearner.objects.get().first_name, "Alicia")


class CombinedCertificateAdminTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser("admin@x.com", "Sup3r-secret!", full_name="Admin")
        self.client = APIClient()
        self.client.force_authenticate(self.staff)
        make_course("word")
        make_course("excel")
        self.learner = OfflineLearner.objects.create(
            client_id=uuid.uuid4(), first_name="Alice", last_name="Uwimana", country="Rwanda",
            date_of_birth=date.fromisoformat(years_ago(11)), grade="P5", is_student=True, school="Kigali Primary",
            registered_by=self.staff,
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
        self.assertEqual(cert.course_titles, ["Demo Course", "Demo Course"])
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
        self.assertEqual(APIClient().get(f"/api/offline-certificates/{code}/pdf/").status_code, 403)

    def test_public_verify_finds_the_combined_certificate(self):
        self.issue()
        code = OfflineCertificate.objects.get().code
        r = APIClient().get(f"/api/certificates/verify/{code}/").json()
        self.assertTrue(r["valid"])
        self.assertEqual(r["learner_name"], "Alice Uwimana")
        self.assertIn("Demo Course", r["course"])

    def test_the_certificate_shows_a_corrected_name_after_an_edit(self):
        self.issue()
        OfflineLearner.objects.update(first_name="Alicia")
        code = OfflineCertificate.objects.get().code
        self.assertEqual(APIClient().get(f"/api/certificates/verify/{code}/").json()["learner_name"], "Alicia Uwimana")
