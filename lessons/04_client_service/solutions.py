"""Module 4 worked answers."""

import time

import requests

from vax_server import REQUIRED


def post_with_backoff(post, url, payload, headers=None, timeout=2.0, retries=4, base_delay=0.5, sleep=time.sleep):
    for attempt in range(retries + 1):
        try:
            return post(url, json=payload, headers=headers, timeout=timeout)
        except (requests.Timeout, requests.ConnectionError):
            if attempt == retries:
                raise
            sleep(base_delay * 2 ** attempt)


def record_dose_checked(store, payload, key):
    fields = {k: payload[k] for k in REQUIRED}
    with store.lock:
        if key is None:
            return store.add(payload), 201
        if key in store.replies:
            first_payload, first_reply = store.replies[key]
            if {k: first_payload[k] for k in REQUIRED} == fields:
                return first_reply, 200
            return {"error": f"idempotency key {key!r} was already used for a different dose"}, 409
        dose = store.add(payload)
        store.replies[key] = (fields, dose)
        return dose, 201


def dose_total_for_dashboard(fetch):
    try:
        return len(fetch("/doses"))
    except requests.RequestException:
        return None
    # Why the dashboard crashing no longer takes VaxRecords down: they are now
    # separate programs that share nothing but messages. A dashboard bug can
    # kill the dashboard's process, but VaxRecords runs in its own process with
    # its own memory, so it keeps recording doses; at worst it stops getting
    # requests from the dashboard. This is enforced modularity. In one Flask
    # process (soft modularity) an infinite loop, a memory blow-up or a crash
    # in the dashboard code would stop dose recording too, and a stray write
    # could even corrupt the dose list directly. The price is that every call
    # between them can now fail or time out, which is why this function must
    # handle an unreachable service.
