"""Capstone worked answers."""

import hashlib
import json


def accept(message, seen):
    key = (message["clinic_id"], message["seq"])
    if key in seen:
        return False
    seen.add(key)
    return True


def _sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def read_verified(replica_paths):
    good, bad = None, []
    for path in replica_paths:
        try:
            record = json.loads(path.read_text())
            if _sha(record["payload"]) == record["sha256"]:
                good = good or record
                continue
        except (OSError, ValueError, KeyError):
            pass
        bad.append(path)
    if good is None:
        raise ValueError(f"no intact replica among {[str(p) for p in replica_paths]}")
    for path in bad:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(good, sort_keys=True))
    return good["payload"]


def authorize(user, action, district_id):
    if not user:
        return False
    verb, target = action
    if user.get("role") == "clinic":
        return verb == "submit" and target == user.get("clinic_id")
    if user.get("role") == "district_officer":
        return verb == "read" and target == user.get("district_id")
    return False
