"""Locust workload for Linklet's public redirect endpoint.

The default profile uses one request per user per second. Running three users
therefore targets approximately 3 redirect requests per second; tune the
user count or ``LINKLET_REDIRECT_WAIT_SECONDS`` for other profiles.
"""

import os

from locust import HttpUser, between, task


SHORT_CODE = "hvkYPbB"
EXPECTED_STATUS = int(os.getenv("LINKLET_EXPECTED_REDIRECT_STATUS", "307"))
WAIT_SECONDS = float(os.getenv("LINKLET_REDIRECT_WAIT_SECONDS", "1"))


class RedirectUser(HttpUser):
    """Repeatedly resolve one pre-seeded short code."""

    # Keep the default close to one request per second per simulated user.
    wait_time = between(max(0.0, WAIT_SECONDS * 0.9), max(0.0, WAIT_SECONDS * 1.1))

    def on_start(self) -> None:
        if not SHORT_CODE:
            raise RuntimeError("A load-test short code must be configured.")

    @task
    def resolve_redirect(self) -> None:
        # Do not follow the Location header: measure Linklet, not the destination site.
        with self.client.get(
            f"/{SHORT_CODE}",
            name="GET /{short_code}",
            allow_redirects=False,
            catch_response=True,
        ) as response:
            if response.status_code != EXPECTED_STATUS:
                response.failure(f"expected HTTP {EXPECTED_STATUS}, got {response.status_code}")
            elif not response.headers.get("Location"):
                response.failure("redirect response has no Location header")
