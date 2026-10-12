"""Capstone exercises. Complete each TODO, then run:

    pytest lessons/12_capstone
    python lessons/12_capstone/bad_week.py
"""

import hashlib
import json


def accept(message: dict, seen: set) -> bool:
    """Decide whether a report message is new, and remember it if so.

    A message is identified by (clinic_id, seq). Retries and late duplicates
    must return False; a new message is added to ``seen`` and returns True.
    Out-of-order arrival is fine: seq 3 before seq 1 is two different messages.
    (Modules 4 and 7.)
    """
    # TODO
    raise NotImplementedError


def read_verified(replica_paths: list) -> dict:
    """Return the payload of the first replica whose checksum matches its content.

    Each file holds {"payload": {...}, "sha256": "..."} where sha256 is
    hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest().
    Repair: rewrite every bad replica with the good record. If no replica is
    good, raise ValueError (fail fast, never return a wrong number). (Module 8.)
    """
    # TODO
    raise NotImplementedError


def authorize(user, action: tuple, district_id) -> bool:
    """Least privilege, with a fail-safe default (Module 11).

    ``user`` is None or {"role": "clinic", "clinic_id": ...} or
    {"role": "district_officer", "district_id": ...}.
    ``action`` is ("submit", clinic_id) or ("read", district_id).

    - Clinic users may only submit reports for their own clinic.
    - District officers may only read their own district.
    - Everything else, including unknown roles and anonymous users, is denied.
    """
    # TODO
    raise NotImplementedError
