"""The capstone system: SurveilLite's report intake as a small, resilient service.

Clinics POST weekly case reports. Each report is stored twice (two replicas)
with a checksum. District officers GET incidence for their own district.

Three decisions are pluggable, passed in as a ``parts`` object with three
functions. Those functions are what you write in the capstone exercises:

    parts.accept(message, seen)                  -> bool   (Modules 4 and 7: idempotence, duplicates)
    parts.read_verified(replica_paths)           -> dict   (Module 8: detect and repair corruption)
    parts.authorize(user, action, district_id)   -> bool   (Module 11: least privilege, complete mediation)

``NaiveParts`` below is what a first version usually does. bad_week.py shows
what goes wrong with it.
"""

import hashlib
import json
from pathlib import Path

from flask import Flask, jsonify, request

from course.data import DISTRICTS, clinics

CLINIC_DISTRICT = dict(zip(clinics().clinic_id, clinics().district_id))
POPULATION = dict(zip(DISTRICTS.district_id, DISTRICTS.population))


def checksum(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def write_replicas(paths, payload):
    """Write the same record, wrapped with its checksum, to every replica path."""
    record = json.dumps({"payload": payload, "sha256": checksum(payload)}, sort_keys=True)
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(record)
        tmp.replace(path)  # all-or-nothing per replica (Module 9)


class NaiveParts:
    @staticmethod
    def accept(message, seen):
        return True  # every delivery counts, including retries

    @staticmethod
    def read_verified(replica_paths):
        return json.loads(replica_paths[0].read_text())["payload"]  # trust the first copy

    @staticmethod
    def authorize(user, action, district_id):
        return user is not None  # any logged-in user may do anything


def create_app(parts, data_dir, users):
    """``users`` maps a bearer token to {"name", "role", and "clinic_id" or "district_id"}."""
    app = Flask(__name__)
    app.config["PROPAGATE_EXCEPTIONS"] = True  # let errors in your parts surface, not become HTTP 500s
    data_dir = Path(data_dir)
    seen = set()       # message keys already accepted
    deliveries = [0]   # every accepted delivery is stored as a new record, like an append-only intake log
    audit = []         # (user name, action, target, allowed)
    app.config["AUDIT"] = audit

    def current_user():
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        return users.get(token)

    def replica_paths(report_key):
        return [data_dir / f"replica{i}" / f"{report_key}.json" for i in (1, 2)]

    @app.post("/reports")
    def submit_report():
        user = current_user()
        msg = request.get_json()
        district_id = CLINIC_DISTRICT.get(msg.get("clinic_id"))
        allowed = parts.authorize(user, ("submit", msg.get("clinic_id")), district_id)
        audit.append((user and user["name"], "submit", msg.get("clinic_id"), allowed))
        if not allowed:
            return jsonify(error="forbidden"), 403
        if not parts.accept(msg, seen):
            return jsonify(status="duplicate ignored"), 200
        deliveries[0] += 1
        key = f"{msg['clinic_id']}_{msg['seq']}_d{deliveries[0]}"
        write_replicas(replica_paths(key), msg)
        return jsonify(status="stored", key=key), 201

    @app.get("/districts/<district_id>/incidence")
    def incidence(district_id):
        user = current_user()
        allowed = parts.authorize(user, ("read", district_id), district_id)
        audit.append((user and user["name"], "read", district_id, allowed))
        if not allowed:
            return jsonify(error="forbidden"), 403
        totals = {}
        for path in sorted((data_dir / "replica1").glob("*.json")):
            rec = parts.read_verified(replica_paths(path.stem))
            if CLINIC_DISTRICT[rec["clinic_id"]] == district_id:
                totals[rec["disease"]] = totals.get(rec["disease"], 0) + rec["cases"]
        rates = {d: round(c / POPULATION[district_id] * 100_000, 2) for d, c in totals.items()}
        return jsonify(district_id=district_id, cases=totals, per_100k=rates)

    return app
