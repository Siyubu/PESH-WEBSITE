import uuid
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from exams.models import ExamAttempt
from rest_framework.test import APIClient

from courses.models import LessonProgress
from courses.tests import make_course
from exams.tests import make_exam, pass_exam

from . import momo
from .models import Certificate, Payment

User = get_user_model()
MOMO = {
    "BASE_URL": "https://momo.test", "TARGET_ENVIRONMENT": "sandbox", "CURRENCY": "EUR",
    "SUBSCRIPTION_KEY": "s", "API_USER": "u", "API_KEY": "k", "USE_CALLBACK": False,
}


@override_settings(MOMO=MOMO, CERTIFICATE_PRICE=20000)
class CertificateFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user("amina@x.com", "Sup3r-secret!", full_name="Amina Uwase")
        self.client.force_authenticate(self.user)
        self.course = make_course("excel", lessons=2)
        self.exam = make_exam(self.course)

    def finish_lessons(self):
        for l in self.course.lessons.all():
            LessonProgress.objects.create(user=self.user, lesson=l)

    def complete_course(self):
        """Lessons done AND exam passed: the two things a certificate needs."""
        self.finish_lessons()
        pass_exam(self.user, self.exam)

    def pay(self, phone="0788123456"):
        return self.client.post("/api/certificates/excel/pay/", {"phone": phone}, format="json")

    def test_phone_normalisation(self):
        self.assertEqual(momo.normalize_rwanda_phone("+250 788 123 456"), "250788123456")
        self.assertEqual(momo.normalize_rwanda_phone("0791234567"), "250791234567")
        self.assertIsNone(momo.normalize_rwanda_phone("0722123456"))
        self.assertIsNone(momo.normalize_rwanda_phone("12"))

    def test_cannot_pay_before_finishing_course(self):
        with mock.patch.object(momo, "request_to_pay") as rtp:
            self.assertEqual(self.pay().status_code, 403)
            rtp.assert_not_called()

    def test_cannot_pay_with_lessons_done_but_exam_not_passed(self):
        self.finish_lessons()
        with mock.patch.object(momo, "request_to_pay") as rtp:
            self.assertEqual(self.pay().status_code, 403)
            rtp.assert_not_called()
        s = self.client.get("/api/certificates/excel/status/").json()
        self.assertTrue(s["lessons_complete"])
        self.assertFalse(s["exam_passed"])
        self.assertFalse(s["eligible"])

    def test_failed_exam_attempt_does_not_unlock_payment(self):
        self.finish_lessons()
        ExamAttempt.objects.create(
            user=self.user, exam=self.exam, status="submitted", expires_at=timezone.now(), submitted_at=timezone.now(),
            correct_count=1, total=4, percent=25, passed=False,
        )
        self.assertEqual(self.pay().status_code, 403)

    def test_bad_phone_rejected(self):
        self.complete_course()
        self.assertEqual(self.pay("123").status_code, 400)

    def test_requires_login(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/certificates/excel/status/").status_code, 403)

    def test_server_sets_price_and_certificate_only_after_momo_success(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay") as rtp, mock.patch.object(momo, "get_status") as gs:
            r = self.client.post("/api/certificates/excel/pay/", {"phone": "0788123456", "amount": 1}, format="json")
            self.assertEqual(r.status_code, 202)
            kw = rtp.call_args.kwargs
            self.assertEqual(kw["amount"], 20000)
            self.assertEqual(kw["phone"], "250788123456")

            gs.return_value = {"status": "PENDING"}
            s = self.client.get("/api/certificates/excel/status/").json()
            self.assertEqual((s["payment_status"], s["certificate"]), ("pending", None))
            self.assertTrue(s["eligible"])

            gs.return_value = {"status": "SUCCESSFUL", "amount": "5"}
            self.assertIsNone(self.client.get("/api/certificates/excel/status/").json()["certificate"])

            gs.return_value = {"status": "SUCCESSFUL", "amount": "20000"}
            s = self.client.get("/api/certificates/excel/status/").json()
            self.assertEqual(s["payment_status"], "successful")
            self.assertRegex(s["certificate"]["code"], r"^PESH-EXCE-[0-9A-F]{8}$")
            self.assertEqual(s["certificate"]["learner_name"], "Amina Uwase")

        self.assertEqual(Certificate.objects.count(), 1)
        self.assertEqual(self.pay().status_code, 409)

    def test_failed_payment_can_be_retried(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay"), mock.patch.object(momo, "get_status") as gs:
            self.pay()
            gs.return_value = {"status": "FAILED", "reason": "REJECTED"}
            self.assertEqual(self.client.get("/api/certificates/excel/status/").json()["payment_status"], "failed")
            self.assertEqual(self.pay().status_code, 202)
        self.assertEqual(Payment.objects.count(), 2)

    def test_rapid_second_request_is_blocked(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay") as rtp:
            self.assertEqual(self.pay().status_code, 202)
            self.assertEqual(self.pay().status_code, 429)
            self.assertEqual(rtp.call_count, 1)

    def test_gateway_error_marks_payment_failed(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay", side_effect=momo.MomoError("down")):
            self.assertEqual(self.pay().status_code, 502)
        self.assertEqual(Payment.objects.get().status, "failed")

    def test_callback_rechecks_with_momo_and_ignores_body(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay"), mock.patch.object(momo, "get_status") as gs:
            self.pay()
            ref = Payment.objects.get().reference
            gs.return_value = {"status": "PENDING"}
            anon = APIClient()
            r = anon.put(f"/api/momo/callback/{ref}/", {"status": "SUCCESSFUL", "amount": "20000"}, format="json")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(Certificate.objects.count(), 0)  # body alone never issues a certificate
            gs.return_value = {"status": "SUCCESSFUL", "amount": "20000"}
            anon.put(f"/api/momo/callback/{ref}/", {}, format="json")
            self.assertEqual(Certificate.objects.count(), 1)
            self.assertEqual(anon.put(f"/api/momo/callback/{uuid.uuid4()}/", {}, format="json").status_code, 200)

    def test_verify_and_pdf(self):
        self.complete_course()
        with mock.patch.object(momo, "request_to_pay"), mock.patch.object(momo, "get_status") as gs:
            self.pay()
            gs.return_value = {"status": "SUCCESSFUL", "amount": "20000"}
            code = self.client.get("/api/certificates/excel/status/").json()["certificate"]["code"]
        anon = APIClient()
        v = anon.get(f"/api/certificates/verify/{code.lower()}/").json()
        self.assertTrue(v["valid"])
        self.assertEqual(v["learner_name"], "Amina Uwase")
        self.assertEqual(anon.get("/api/certificates/verify/PESH-NOPE-00000000/").status_code, 404)
        pdf = self.client.get("/api/certificates/excel/pdf/")
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertEqual(anon.get("/api/certificates/excel/pdf/").status_code, 403)

    def test_payments_disabled_without_credentials(self):
        self.complete_course()
        with override_settings(MOMO={**MOMO, "API_KEY": ""}):
            self.assertEqual(self.pay().status_code, 503)
