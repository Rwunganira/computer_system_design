"""Module 4 exercises. Complete each TODO, then run: pytest lessons/04_client_service"""

import time

import requests


def post_with_backoff(post, url, payload, headers=None, timeout=2.0, retries=4, base_delay=0.5, sleep=time.sleep):
    """Send ``payload`` with ``post`` and return the response, retrying on timeouts.

    Call it as ``post(url, json=payload, headers=headers, timeout=timeout)``,
    just like ``requests.post``. If that raises ``requests.Timeout`` or
    ``requests.ConnectionError``, wait and try again: wait ``base_delay`` seconds
    after the first failure, then twice as long after each further failure
    (0.5, 1, 2, 4 ...). Use ``sleep`` to wait, so tests need not really sleep.

    Make at most ``retries`` retries (``retries + 1`` attempts in all). If the
    last attempt fails too, re-raise its exception. Any other exception is not a
    network failure: let it propagate at once, without retrying.
    """
    # TODO
    raise NotImplementedError


def record_dose_checked(store, payload, key):
    """A stricter version of ``vax_server.record_dose``. Return (body, status).

    ``store`` is a ``vax_server.DoseStore``: ``store.add(payload)`` records a
    dose and returns it; ``store.replies`` maps each idempotency key to
    ``(payload, reply body)``; hold ``store.lock`` while you check and record.

    - No key (``key is None``): record the dose, return (dose, 201).
    - A new key: record the dose, remember the reply under the key, return (dose, 201).
    - A key seen before with the same dose fields (person_id, vaccine,
      clinic_id, dose_date): record nothing, return the first reply with 200.
    - A key seen before with *different* dose fields: the client has a bug and
      is reusing keys. Record nothing; return ({"error": "..."}, 409).
    """
    # TODO
    raise NotImplementedError


def dose_total_for_dashboard(fetch):
    """The number of doses VaxRecords holds, or None if it cannot be reached.

    ``fetch(path)`` asks the service for ``path`` (here ``"/doses"``) and returns
    the decoded JSON list, or raises ``requests.RequestException`` when the
    service is down or slow. The dashboard must show "unavailable" rather than
    crash, so return None in that case.
    """
    # TODO
    raise NotImplementedError
    # TODO (not tested): in a comment here, explain why a bug that crashes the
    # dashboard no longer takes VaxRecords down with it, and what would happen
    # if both still ran as functions in one Flask process.
