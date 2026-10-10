from rest_framework.authentication import SessionAuthentication


class StrictCsrfSessionAuthentication(SessionAuthentication):
    """DRF normally skips the CSRF check for anonymous requests; we want it for login/register too."""

    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            self.enforce_csrf(request)
        return result
