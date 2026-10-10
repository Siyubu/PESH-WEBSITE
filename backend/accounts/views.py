from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .authentication import StrictCsrfSessionAuthentication
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class ThrottledView(APIView):
    authentication_classes = [StrictCsrfSessionAuthentication]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SessionView(APIView):
    """GET: who am I? Also sets the CSRF cookie the frontend needs for later POSTs."""

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data if request.user.is_authenticated else None})


class RegisterView(ThrottledView):
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        login(request, user)
        return Response({"user": UserSerializer(user).data}, status=201)


class LoginView(ThrottledView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = authenticate(request, username=email, password=request.data.get("password", ""))
        if user is None:
            return Response({"error": "Wrong email or password."}, status=400)
        login(request, user)
        return Response({"user": UserSerializer(user).data})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({"user": None})


class PasswordResetView(ThrottledView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.SITE_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                "Reset your PESH password",
                f"Hello {user.full_name},\n\nUse this link to choose a new password:\n{link}\n\n"
                "If you did not ask for this, you can ignore this email.",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        # Same answer either way so the endpoint cannot be used to find registered emails.
        return Response({"ok": True})


class PasswordResetConfirmView(ThrottledView):
    def post(self, request):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(request.data.get("uid", ""))))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if user is None or not default_token_generator.check_token(user, request.data.get("token", "")):
            return Response({"error": "This reset link is invalid or has expired."}, status=400)
        password = request.data.get("password", "")
        try:
            validate_password(password, user)
        except ValidationError as e:
            return Response({"error": " ".join(e.messages)}, status=400)
        user.set_password(password)
        user.save()
        return Response({"ok": True})
