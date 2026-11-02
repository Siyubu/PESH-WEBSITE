import uuid

from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.authentication import ExpiringTokenAuthentication
from certificates.pdf import combined_certificate_pdf

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
        # A fresh token on every login, so the 24h clock restarts and a leaked old token stops working.
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response({"token": token.key, "staff_name": user.full_name})


class OfflineLearnerSyncView(APIView):
    """Create-or-update a learner by the phone-generated client_id, so retried and edited syncs are safe.

    A repeat of an already-synced version changes nothing. An edit (newer client_updated_at) overwrites the
    server copy; an older one arriving late (two sync workers racing) is ignored.
    """

    authentication_classes = [ExpiringTokenAuthentication]
    permission_classes = [IsAdminUser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mobile"

    def post(self, request):
        try:
            client_id = uuid.UUID(str(request.data.get("client_id")))
        except ValueError:
            return Response({"client_id": ["A valid UUID is required."]}, status=400)

        for _ in range(2):
            with transaction.atomic():
                existing = OfflineLearner.objects.select_for_update().filter(client_id=client_id).first()
                if existing:
                    return self._update(existing, request.data)
            ser = OfflineLearnerSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            try:
                with transaction.atomic():
                    obj = ser.save(registered_by=request.user)
            except IntegrityError:
                continue  # another sync created it a moment ago: go round again and apply ours as an update
            return Response(OfflineLearnerSerializer(obj).data, status=201)
        return Response({"error": "Could not save this learner. Please try again."}, status=409)

    def _update(self, existing, data):
        ser = OfflineLearnerSerializer(existing, data=data)
        ser.is_valid(raise_exception=True)
        incoming = ser.validated_data.get("client_updated_at")
        if incoming is None or incoming <= existing.client_updated_at:
            return Response(OfflineLearnerSerializer(existing).data, status=200)
        ser.validated_data.pop("created_at", None)
        obj = ser.save()
        return Response(OfflineLearnerSerializer(obj).data, status=200)


class OfflineCertificatePdfView(APIView):
    """Admin-only download, linked from the Django admin change page."""

    permission_classes = [IsAdminUser]

    def get(self, request, code):
        cert = get_object_or_404(OfflineCertificate.objects.select_related("learner"), code=code.upper())
        resp = HttpResponse(combined_certificate_pdf(cert), content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="{cert.code}.pdf"'
        return resp
