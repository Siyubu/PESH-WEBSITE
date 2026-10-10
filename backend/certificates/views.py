from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from courses.services import is_course_complete, published_courses
from exams.services import has_passed

from . import momo, services
from .models import Certificate, Payment
from .pdf import certificate_pdf


def cert_data(cert):
    return {
        "code": cert.code,
        "learner_name": cert.learner_name,
        "course": cert.course.title,
        "course_slug": cert.course.slug,
        "issued_at": cert.issued_at.isoformat(),
    }


class MyCertificatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certs = Certificate.objects.filter(user=request.user).select_related("course")
        return Response([cert_data(c) for c in certs])


class CertificateStatusView(APIView):
    """Everything the certificate page needs. Also re-checks a pending payment with MoMo."""

    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        course = get_object_or_404(published_courses(), slug=slug)
        cert = Certificate.objects.filter(user=request.user, course=course).first()
        payment = Payment.objects.filter(user=request.user, course=course).first()
        if payment and payment.status == Payment.PENDING:
            payment = services.sync_payment(payment)
            cert = cert or Certificate.objects.filter(user=request.user, course=course).first()
        return Response(
            {
                "course": {"slug": course.slug, "title": course.title, "lesson_count": course.lessons.count()},
                "lessons_complete": is_course_complete(request.user, course),
                "exam_passed": has_passed(request.user, course),
                "eligible": services.eligibility(request.user, course),
                "price": settings.CERTIFICATE_PRICE,
                "payments_enabled": momo.configured(),
                "payment_status": payment.status if payment else None,
                "certificate": cert_data(cert) if cert else None,
            }
        )


class PayView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "pay"

    def post(self, request, slug):
        course = get_object_or_404(published_courses(), slug=slug)
        phone = momo.normalize_rwanda_phone(request.data.get("phone"))
        if not phone:
            return Response({"error": "Enter a valid MTN Rwanda number, for example 0788123456."}, status=400)
        if not services.eligibility(request.user, course):
            return Response({"error": "Finish all lessons and pass the final exam before paying for the certificate."}, status=403)
        if Certificate.objects.filter(user=request.user, course=course).exists():
            return Response({"error": "You already have this certificate."}, status=409)
        recent = timezone.now() - timedelta(seconds=45)
        if Payment.objects.filter(user=request.user, course=course, status=Payment.PENDING, created_at__gte=recent).exists():
            return Response({"error": "A payment request was just sent. Please wait a moment."}, status=429)
        if not momo.configured():
            return Response({"error": "Payments are not switched on yet. Please check back soon."}, status=503)
        try:
            services.start_payment(request.user, course, phone)
        except momo.MomoError:
            return Response({"error": "Could not start the payment. Please try again in a moment."}, status=502)
        return Response({"payment_status": Payment.PENDING}, status=202)


class CertificatePdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        cert = get_object_or_404(Certificate.objects.select_related("course"), user=request.user, course__slug=slug)
        resp = HttpResponse(certificate_pdf(cert), content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{cert.code}.pdf"'
        return resp


class VerifyView(APIView):
    def get(self, request, code):
        code = code.upper()
        cert = Certificate.objects.filter(code=code).select_related("course").first()
        if cert:
            return Response({"valid": True, **cert_data(cert)})
        from offline_enrollment.models import OfflineCertificate

        offline = OfflineCertificate.objects.filter(code=code).select_related("learner").first()
        if offline:
            return Response(
                {
                    "valid": True,
                    "code": offline.code,
                    "learner_name": offline.learner.full_name(),
                    "course": " + ".join(offline.course_titles),
                    "course_slug": None,
                    "issued_at": offline.issued_at.isoformat(),
                }
            )
        return Response({"valid": False}, status=404)


@method_decorator(csrf_exempt, name="dispatch")
class MomoCallbackView(APIView):
    """MoMo calls this when a payment finishes. We ignore the body and re-ask MoMo directly."""

    authentication_classes = []

    def _handle(self, reference):
        payment = Payment.objects.filter(reference=reference).first()
        if payment:
            services.sync_payment(payment)
        return Response({"ok": True})

    def put(self, request, reference):
        return self._handle(reference)

    def post(self, request, reference):
        return self._handle(reference)
