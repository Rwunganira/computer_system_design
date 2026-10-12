"""Module 11 exercises. Complete each TODO, then run: pytest lessons/11_security"""

import hashlib
import json

import vax_api_insecure  # the leaky first version of VaxRecords, in this folder


# --- 1. Fix the record-access bug -------------------------------------------

def can_read(user, patient):
    """May ``user`` read ``patient``'s record?

    ``user`` is a dict like {"role": "district_officer", "district": "N-CEN"} or
    {"role": "national"}; ``patient`` has a "district_id". National staff read
    everything; a district officer reads only their own district. Apply
    fail-safe defaults: anything you did not explicitly allow is denied.
    """
    # TODO
    raise NotImplementedError


def create_app():
    """VaxRecords with your access check plugged in (no TODO here)."""
    return vax_api_insecure.create_app(access_check=can_read)


# --- 2. A tamper-evident audit log -------------------------------------------

GENESIS = "0" * 64  # the "previous hash" of the first entry


def entry_hash(prev_hash, entry):
    """SHA-256 over the previous hash and the entry, as hex (no TODO here)."""
    return hashlib.sha256((prev_hash + json.dumps(entry, sort_keys=True)).encode()).hexdigest()


def append_entry(log, entry):
    """Append ``entry`` (a dict) to ``log`` (a list) and return the new hash.

    Each item of ``log`` is {"entry": entry, "prev": <hash of the item before,
    or GENESIS>, "hash": entry_hash(prev, entry)}.
    """
    # TODO
    raise NotImplementedError


def verify_chain(log, head=None):
    """True if no item in ``log`` was altered, removed or reordered.

    Check that each item's "prev" is the previous item's "hash" (GENESIS for
    the first) and that each "hash" really is entry_hash(prev, entry). If
    ``head`` is given, the last hash must equal it: keeping the latest hash
    somewhere else is what catches an attacker who cuts entries off the end.
    """
    # TODO
    raise NotImplementedError


# --- 3. A threat model --------------------------------------------------------

PRINCIPLES = [
    "open design",
    "fail-safe defaults",
    "least privilege",
    "complete mediation",
    "economy of mechanism",
    "psychological acceptability",
]


def threat_model():
    """A one-page threat model for VaxRecords, as data.

    Return {"assets": [str, ...], "adversaries": [str, ...],
            "controls": [{"threat": str, "control": str, "principle": str}, ...]}
    with at least 3 assets, 3 adversaries and 5 controls. Each control's
    "principle" is one of PRINCIPLES, and between them they use at least 4.
    """
    # TODO: hint, start from what the example protects and who it protects it from.
    raise NotImplementedError
