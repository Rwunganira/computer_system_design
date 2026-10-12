"""A VaxRecords client: records doses by sending messages to the service.

A local call ``record_dose(...)`` either runs or raises. A remote call has a
third outcome: no answer. When the reply does not come back in time, the
client cannot tell whether

  * the request was lost (the dose was NOT recorded), or
  * the reply was lost (the dose WAS recorded).

The naive client retries anyway, which gives *at-least-once* semantics: every
dose is recorded, some of them twice. The safe client sends the same
idempotency key with every retry of one dose, and the service records each key
at most once, so retries are harmless.
"""

import time
import uuid

import requests


class VaxClient:
    """Talks to a VaxRecords service at ``base_url``.

    ``idempotent=False`` is the naive client; ``idempotent=True`` attaches an
    idempotency key. ``post`` is the transport, normally ``requests.post``; tests
    can pass a fake one.
    """

    def __init__(self, base_url, idempotent=False, timeout=0.25, retries=5, post=requests.post):
        self.base_url = base_url.rstrip("/")
        self.idempotent = idempotent
        self.timeout = timeout
        self.retries = retries
        self.post = post
        self.timeouts_seen = 0

    def record_dose(self, dose):
        """Send one dose, retrying on timeout. Returns the service's reply."""
        # One key per *dose*, created before the first attempt and reused by
        # every retry. A new key per attempt would defeat the purpose.
        headers = {"Idempotency-Key": str(uuid.uuid4())} if self.idempotent else {}
        for attempt in range(self.retries + 1):
            try:
                reply = self.post(f"{self.base_url}/doses", json=dose,
                                  headers=headers, timeout=self.timeout)
                reply.raise_for_status()
                return reply.json()
            except (requests.Timeout, requests.ConnectionError):
                self.timeouts_seen += 1
                time.sleep(0.01 * 2 ** attempt)  # brief backoff before trying again
        raise TimeoutError(f"no reply after {self.retries + 1} attempts")
