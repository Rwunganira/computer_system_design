"""The VaxRecords service: a Flask app that records vaccine doses.

It runs as its own program (or thread) and is reached only by HTTP messages,
which is what the book calls enforced modularity: a client cannot reach in and
corrupt the dose list, and a client that crashes cannot take the service down.

To make the network's failures visible, ``drop_rate`` makes the service save
a dose and then "lose" the reply: it stalls until the client has given up
waiting. To the client, a reply that arrives too late looks exactly like a
request that never arrived. The drops come from a seeded random generator, so
every run drops the same requests.

    app = create_app(drop_rate=0.3, seed=4)
    app.test_client().post("/doses", json={...}, headers={"Idempotency-Key": "..."})
"""

import random
import threading
import time

from flask import Flask, jsonify, request

REQUIRED = ("person_id", "vaccine", "clinic_id", "dose_date")


class DoseStore:
    """The service's memory: every dose it has recorded, plus the replies it
    has already sent for each idempotency key."""

    def __init__(self):
        self.doses = []
        self.replies = {}              # idempotency key -> (payload, reply body)
        self.lock = threading.Lock()   # Flask may serve requests on several threads

    def add(self, payload):
        """Record one dose and return it with its new dose_id."""
        dose = {"dose_id": len(self.doses) + 1, **{k: payload[k] for k in REQUIRED}}
        self.doses.append(dose)
        return dose


def record_dose(store, payload, key):
    """Record a dose, returning (body, status).

    If the request carries an idempotency key the service has seen before, it
    replays the reply it sent the first time instead of recording a second dose.
    Without a key, every request records a new dose.
    """
    with store.lock:  # check-then-record must not interleave with another request
        if key is not None and key in store.replies:
            return store.replies[key][1], 200
        dose = store.add(payload)
        if key is not None:
            store.replies[key] = (payload, dose)
        return dose, 201


def create_app(store=None, drop_rate=0.0, seed=4, drop_delay=1.0, handler=record_dose):
    """Build the VaxRecords app.

    ``handler(store, payload, key) -> (body, status)`` does the recording, so an
    exercise can swap in its own version. With probability ``drop_rate`` the app
    saves the dose and then stalls for ``drop_delay`` seconds before replying.
    """
    app = Flask(__name__)
    app.config["store"] = store = store if store is not None else DoseStore()
    rng = random.Random(seed)

    @app.post("/doses")
    def post_dose():
        payload = request.get_json(silent=True) or {}
        missing = [k for k in REQUIRED if k not in payload]
        if missing:
            return jsonify(error=f"missing fields: {', '.join(missing)}"), 400
        body, status = handler(store, payload, request.headers.get("Idempotency-Key"))
        if status < 300 and rng.random() < drop_rate:
            time.sleep(drop_delay)  # the dose is saved, but the reply is "lost"
        return jsonify(body), status

    @app.get("/doses")
    def list_doses():
        return jsonify(store.doses)

    @app.get("/persons/<person_id>/doses")
    def person_doses(person_id):
        return jsonify([d for d in store.doses if d["person_id"] == person_id])

    return app


if __name__ == "__main__":
    # Run the service on its own: python lessons/04_client_service/vax_server.py
    create_app(drop_rate=0.3).run(port=5004, threaded=True)
