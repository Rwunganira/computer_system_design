"""Module 11 worked answers."""

import hashlib
import json

import vax_api_insecure


def can_read(user, patient):
    role = user.get("role")
    if role == "national":
        return True
    if role == "district_officer" and user.get("district"):
        return user["district"] == patient.get("district_id")
    return False  # fail-safe default: unknown roles and incomplete users get nothing


def create_app():
    return vax_api_insecure.create_app(access_check=can_read)


GENESIS = "0" * 64


def entry_hash(prev_hash, entry):
    return hashlib.sha256((prev_hash + json.dumps(entry, sort_keys=True)).encode()).hexdigest()


def append_entry(log, entry):
    prev = log[-1]["hash"] if log else GENESIS
    h = entry_hash(prev, entry)
    log.append({"entry": entry, "prev": prev, "hash": h})
    return h


def verify_chain(log, head=None):
    prev = GENESIS
    for item in log:
        if item["prev"] != prev or item["hash"] != entry_hash(prev, item["entry"]):
            return False
        prev = item["hash"]
    return head is None or prev == head


PRINCIPLES = [
    "open design",
    "fail-safe defaults",
    "least privilege",
    "complete mediation",
    "economy of mechanism",
    "psychological acceptability",
]


def threat_model():
    return {
        "assets": [
            "children's vaccination records (identity, birth date, dose history)",
            "user credentials and session tokens",
            "the audit log of who read which record",
            "the service key SurveilLite uses to call VaxRecords",
        ],
        "adversaries": [
            "a curious or malicious district officer reading other districts (insider)",
            "an outsider guessing passwords or replaying stolen tokens",
            "someone on the clinic network altering requests in transit",
            "an administrator covering their tracks by editing the audit log",
        ],
        "controls": [
            {"threat": "officer edits the ID in /patients/<id>",
             "control": "check the record's district against the user's on every read",
             "principle": "complete mediation"},
            {"threat": "a new role or missing field slips through",
             "control": "deny unless a rule explicitly allows",
             "principle": "fail-safe defaults"},
            {"threat": "a stolen officer account exposes the whole country",
             "control": "district officers see only their district; national role is rare",
             "principle": "least privilege"},
            {"threat": "a leaked password database is cracked",
             "control": "salted scrypt hashes, never plaintext",
             "principle": "open design"},
            {"threat": "forged or altered SurveilLite requests",
             "control": "HMAC-SHA256 over method, path, timestamp and body; reject stale timestamps",
             "principle": "open design"},
            {"threat": "insider reads records and denies it, or edits the log",
             "control": "append-only audit log with chained hashes, head kept elsewhere",
             "principle": "economy of mechanism"},
            {"threat": "nurses share one login because logging in is slow",
             "control": "short login, long-enough sessions on clinic tablets",
             "principle": "psychological acceptability"},
        ],
    }
