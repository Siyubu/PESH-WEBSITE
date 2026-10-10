from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from .models import User


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)
        self.client.get("/api/auth/session/")  # sets csrftoken cookie

    def post(self, path, data):
        token = self.client.cookies["csrftoken"].value
        return self.client.post(path, data, format="json", HTTP_X_CSRFTOKEN=token)

    def test_register_login_logout(self):
        r = self.post("/api/auth/register/", {"full_name": "Amina Uwase", "email": "Amina@Example.com", "password": "Sup3r-secret!"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.client.get("/api/auth/session/").json()["user"]["email"], "amina@example.com")
        self.post("/api/auth/logout/", {})
        self.assertIsNone(self.client.get("/api/auth/session/").json()["user"])
        r = self.post("/api/auth/login/", {"email": "AMINA@example.com", "password": "Sup3r-secret!"})
        self.assertEqual(r.status_code, 200)

    def test_requires_csrf_token(self):
        r = self.client.post("/api/auth/register/", {"full_name": "A", "email": "a@x.com", "password": "Sup3r-secret!"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_rejects_duplicate_email_and_weak_password(self):
        User.objects.create_user("a@x.com", "Sup3r-secret!", full_name="A")
        self.assertEqual(self.post("/api/auth/register/", {"full_name": "B", "email": "a@x.com", "password": "Sup3r-secret!"}).status_code, 400)
        self.assertEqual(self.post("/api/auth/register/", {"full_name": "B", "email": "b@x.com", "password": "123"}).status_code, 400)

    def test_wrong_password(self):
        User.objects.create_user("a@x.com", "Sup3r-secret!", full_name="A")
        self.assertEqual(self.post("/api/auth/login/", {"email": "a@x.com", "password": "nope"}).status_code, 400)

    def test_password_reset_flow(self):
        User.objects.create_user("a@x.com", "Sup3r-secret!", full_name="A")
        self.assertEqual(self.post("/api/auth/password-reset/", {"email": "nobody@x.com"}).status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.post("/api/auth/password-reset/", {"email": "a@x.com"})
        self.assertEqual(len(mail.outbox), 1)
        link = [l for l in mail.outbox[0].body.splitlines() if "reset-password" in l][0]
        uid = link.split("uid=")[1].split("&")[0]
        token = link.split("token=")[1]
        self.assertEqual(self.post("/api/auth/password-reset/confirm/", {"uid": uid, "token": "bad", "password": "N3w-secret-pw"}).status_code, 400)
        self.assertEqual(self.post("/api/auth/password-reset/confirm/", {"uid": uid, "token": token, "password": "N3w-secret-pw"}).status_code, 200)
        self.assertEqual(self.post("/api/auth/login/", {"email": "a@x.com", "password": "N3w-secret-pw"}).status_code, 200)
