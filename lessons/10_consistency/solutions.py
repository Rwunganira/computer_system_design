"""Module 10 worked answers."""

import copy

import offline_sync


def lww_loses_a_dose():
    # Perfect clocks. Tablet B records a dose after tablet A, so its timestamp is
    # later and its whole record wins; A's dose was never in B's copy, so it is gone.
    record = {"person_id": "P000001", "doses": {("BCG", "2026-01-05", "C01")},
              "updated_at": 0, "vv": {"server": 1}}
    server = offline_sync.Replica("server", record)
    a = offline_sync.Replica("tablet-A", record)
    b = offline_sync.Replica("tablet-B", record)
    a.record_dose("OPV1", "2026-02-16", "C01", now=600)
    b.record_dose("DTP1", "2026-02-16", "C02", now=660)
    recorded = a.record["doses"] | b.record["doses"]
    offline_sync.lww_sync(server, a)
    offline_sync.lww_sync(server, b)
    return recorded, set(server.record["doses"])


def compare(vv_a, vv_b):
    keys = vv_a.keys() | vv_b.keys()
    a_ahead = any(vv_a.get(k, 0) > vv_b.get(k, 0) for k in keys)
    b_ahead = any(vv_b.get(k, 0) > vv_a.get(k, 0) for k in keys)
    if a_ahead and b_ahead:
        return "concurrent"
    if a_ahead:
        return "after"
    if b_ahead:
        return "before"
    return "equal"


def merge(record_a, record_b):
    merged = copy.deepcopy(record_a)
    merged["doses"] = set(record_a["doses"]) | set(record_b["doses"])
    keys = record_a["vv"].keys() | record_b["vv"].keys()
    merged["vv"] = {k: max(record_a["vv"].get(k, 0), record_b["vv"].get(k, 0)) for k in keys}
    merged["updated_at"] = max(record_a["updated_at"], record_b["updated_at"])
    return merged


FIGURES = [
    "weekly_incidence_map",
    "national_coverage_trend",
    "child_dose_history_at_clinic",
    "vaccine_lot_recall_status",
]


def staleness_policy():
    return {
        "weekly_incidence_map": {
            "stale_ok": True,
            "why": "Weekly aggregates change slowly; an hour-old map leads to the same public health decision.",
        },
        "national_coverage_trend": {
            "stale_ok": True,
            "why": "A monthly trend over thousands of children barely moves when a few late doses arrive.",
        },
        "child_dose_history_at_clinic": {
            "stale_ok": False,
            "why": "A missing recent dose can lead the nurse to vaccinate the child twice; show fresh data or warn it may be stale.",
        },
        "vaccine_lot_recall_status": {
            "stale_ok": False,
            "why": "Using a recalled lot because a replica had not heard of the recall harms a child; this must be strict.",
        },
    }
