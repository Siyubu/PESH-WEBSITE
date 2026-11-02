from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class StrictCsrfSessionAuthentication(SessionAuthentication):
    """DRF normally skips the CSRF check for anonymous requests; we want it for login/register too."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            self.enforce_csrf(request)
        return result


class ExpiringTokenAuthentication(TokenAuthentication):
    """DRF tokens never expire on their own; this rejects (and deletes) any older than the configured maximum."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if timezone.now() - token.created > timedelta(seconds=settings.AUTH_TOKEN_MAX_AGE_SECONDS):
            token.delete()
            raise AuthenticationFailed("This login has expired. Please log in again.")
        return user, token
