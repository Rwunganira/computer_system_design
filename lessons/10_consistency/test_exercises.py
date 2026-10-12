import copy

from course.testing import load_exercises

ex = load_exercises(__file__)


# --- 1. last-writer-wins loses data ------------------------------------------

def test_lww_loses_a_dose():
    recorded, on_server = ex.lww_loses_a_dose()
    assert on_server <= recorded, "the server should not invent doses"
    assert recorded - on_server, "every dose survived: this scenario does not show the loss"


# --- 2. version-vector comparison ------------------------------------------

def test_compare_equal():
    assert ex.compare({"a": 1, "b": 2}, {"b": 2, "a": 1}) == "equal"
    assert ex.compare({}, {}) == "equal"


def test_compare_missing_entries_count_as_zero():
    assert ex.compare({"a": 1, "b": 0}, {"a": 1}) == "equal"
    assert ex.compare({"a": 1}, {"a": 1, "b": 1}) == "before"


def test_compare_before_and_after():
    assert ex.compare({"server": 1}, {"server": 1, "tablet-A": 1}) == "before"
    assert ex.compare({"server": 2, "tablet-A": 1}, {"server": 1}) == "after"


def test_compare_concurrent():
    a = {"server": 1, "tablet-A": 1}
    b = {"server": 1, "tablet-B": 1}
    assert ex.compare(a, b) == "concurrent"
    assert ex.compare(b, a) == "concurrent"


# --- 3. grow-only merge ------------------------------------------------------

def _records():
    base = {("BCG", "2026-01-05", "C01")}
    a = {"person_id": "P000001", "doses": base | {("OPV1", "2026-02-16", "C01")},
         "updated_at": 600, "vv": {"server": 1, "tablet-A": 1}}
    b = {"person_id": "P000001", "doses": base | {("DTP1", "2026-02-16", "C02")},
         "updated_at": 660, "vv": {"server": 1, "tablet-B": 1}}
    return a, b


def test_merge_keeps_every_dose():
    a, b = _records()
    m = ex.merge(a, b)
    assert m["doses"] == a["doses"] | b["doses"]
    assert m["person_id"] == "P000001"
    assert m["updated_at"] == 660


def test_merged_vector_dominates_both():
    a, b = _records()
    m = ex.merge(a, b)
    assert m["vv"] == {"server": 1, "tablet-A": 1, "tablet-B": 1}
    assert ex.compare(m["vv"], a["vv"]) == "after"
    assert ex.compare(m["vv"], b["vv"]) == "after"


def test_merge_is_commutative_and_pure():
    a, b = _records()
    a0, b0 = copy.deepcopy(a), copy.deepcopy(b)
    assert ex.merge(a, b)["doses"] == ex.merge(b, a)["doses"]
    assert (a, b) == (a0, b0), "merge must not modify its inputs"


# --- 4. which figures tolerate stale data -----------------------------------

def test_staleness_policy():
    policy = ex.staleness_policy()
    assert set(policy) == set(ex.FIGURES)
    for figure, decision in policy.items():
        assert isinstance(decision["stale_ok"], bool), figure
        assert len(decision["why"]) >= 20, f"justify {figure} in a sentence"
    assert policy["weekly_incidence_map"]["stale_ok"] is True
    assert policy["vaccine_lot_recall_status"]["stale_ok"] is False
    assert policy["child_dose_history_at_clinic"]["stale_ok"] is False
