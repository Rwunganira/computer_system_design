"""Module 10 exercises. Complete each TODO, then run: pytest lessons/10_consistency"""

import offline_sync  # the example in this folder: Replica, lww_sync, dominates, ...


def lww_loses_a_dose():
    """Build your own scenario in which last-writer-wins sync loses a dose.

    Use ``offline_sync.Replica`` and ``offline_sync.lww_sync``. Start a server and
    two tablets from the same record, record a different dose on each tablet,
    sync both, and return ``(recorded, on_server)``: the set of every dose that
    was recorded anywhere, and the set the server ends up with.

    Challenge: make it lose a dose even though every clock is exactly right
    (``clock_skew=0``). The example's skewed clock is not the real culprit.
    """
    # TODO: hint, a record looks like
    #   {"person_id": "P000001", "doses": {("BCG", "2026-01-05", "C01")},
    #    "updated_at": 0, "vv": {"server": 1}}
    raise NotImplementedError


def compare(vv_a, vv_b):
    """Compare two version vectors (dicts of replica -> count; missing means 0).

    Return "equal" if they are the same, "before" if ``vv_a`` happened before
    ``vv_b`` (b has seen everything a has, and more), "after" if the reverse,
    and "concurrent" if each has seen an update the other has not.
    """
    # TODO
    raise NotImplementedError


def merge(record_a, record_b):
    """Reconcile two versions of the same child's record. Return a NEW record.

    Domain rule: a dose, once given, stays given. Doses form a grow-only set,
    so the merged record has the union of both dose sets. Its version vector
    must have seen everything either input had seen. Keep ``person_id``, and set
    ``updated_at`` to the later of the two. Do not modify the inputs.
    """
    # TODO
    raise NotImplementedError


# Figures shown on the SurveilLite dashboard or used by VaxRecords clients.
FIGURES = [
    "weekly_incidence_map",          # incidence per 100k by district, last 12 weeks
    "national_coverage_trend",       # % of children with MCV1, by month
    "child_dose_history_at_clinic",  # nurse checks a child's doses before vaccinating
    "vaccine_lot_recall_status",     # has this vaccine lot been recalled?
]


def staleness_policy():
    """For each name in FIGURES, decide whether it may be served from a stale
    replica or cache (eventual consistency) or needs fresh data (strict).

    Return {figure: {"stale_ok": bool, "why": "one-sentence justification"}}.
    """
    # TODO
    raise NotImplementedError
