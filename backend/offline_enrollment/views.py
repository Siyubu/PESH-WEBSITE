from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from certificates.pdf import combined_certificate_pdf
from django.http import HttpResponse

from .models import OfflineCertificate, OfflineLearner
from .serializers import OfflineLearnerSerializer


class MobileLoginView(APIView):
    """Staff sign-in for the Android app. Only staff accounts (mentors/admins) may use it."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = authenticate(request, username=email, password=request.data.get("password", ""))
        if user is None or not user.is_staff:
            return Response({"error": "Wrong email or password, or this account cannot use the app."}, status=400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "staff_name": user.full_name})


class OfflineLearnerCreateView(APIView):
    """Registers a learner signed up in person. Idempotent on client_id, so a retried sync is safe."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mobile"

    def post(self, request):
        client_id = request.data.get("client_id")
        existing = OfflineLearner.objects.filter(client_id=client_id).first() if client_id else None
        if existing:
            return Response(OfflineLearnerSerializer(existing).data, status=200)
        ser = OfflineLearnerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            obj = ser.save(registered_by=request.user)
        except IntegrityError:
            # Two sync attempts raced (e.g. the periodic and the on-save sync worker both fired at
            # once): the other one already created this client_id a moment ago. Same record either way.
            obj = OfflineLearner.objects.get(client_id=client_id)
            return Response(OfflineLearnerSerializer(obj).data, status=200)
        return Response(OfflineLearnerSerializer(obj).data, status=201)


class OfflineCertificatePdfView(APIView):
    """Admin-only download, linked from the Django admin change page."""

    permission_classes = [IsAdminUser]

    def get(self, request, code):
        cert = get_object_or_404(OfflineCertificate.objects.select_related("learner"), code=code.upper())
        resp = HttpResponse(combined_certificate_pdf(cert), content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{cert.code}.pdf"'
        return resp
