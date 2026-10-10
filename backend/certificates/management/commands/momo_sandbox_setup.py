import uuid

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a MoMo SANDBOX API user and key from MOMO_SUBSCRIPTION_KEY and print them."

    def handle(self, *args, **opts):
        cfg = settings.MOMO
        if not cfg["SUBSCRIPTION_KEY"]:
            raise CommandError("Set MOMO_SUBSCRIPTION_KEY in .env first.")
        base, key = cfg["BASE_URL"], cfg["SUBSCRIPTION_KEY"]
        user = str(uuid.uuid4())
        r = requests.post(
            f"{base}/v1_0/apiuser",
            headers={"X-Reference-Id": user, "Ocp-Apim-Subscription-Key": key},
            json={"providerCallbackHost": "localhost"},
            timeout=20,
        )
        if r.status_code != 201:
            raise CommandError(f"Creating the API user failed ({r.status_code}): {r.text[:200]}")
        r = requests.post(f"{base}/v1_0/apiuser/{user}/apikey", headers={"Ocp-Apim-Subscription-Key": key}, timeout=20)
        if r.status_code != 201:
            raise CommandError(f"Creating the API key failed ({r.status_code}): {r.text[:200]}")
        self.stdout.write("Add these to .env:\n")
        self.stdout.write(f"MOMO_API_USER={user}")
        self.stdout.write(f"MOMO_API_KEY={r.json()['apiKey']}")
