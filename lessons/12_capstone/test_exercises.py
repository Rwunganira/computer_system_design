import json

import pytest

from course.testing import load_exercises, load_module

ex = load_exercises(__file__)
bad_week = load_module(__file__, "bad_week")
system = load_module(__file__, "surveillance_system")


def test_accept_ignores_retries():
    seen = set()
    m = {"clinic_id": "C31", "seq": 1}
    assert ex.accept(m, seen) is True
    assert ex.accept(dict(m), seen) is False


def test_accept_allows_out_of_order():
    seen = set()
    assert [ex.accept({"clinic_id": "C32", "seq": s}, seen) for s in (3, 1, 2)] == [True, True, True]
    assert ex.accept({"clinic_id": "C31", "seq": 3}, seen) is True  # same seq, other clinic


def test_read_verified_repairs(tmp_path):
    paths = [tmp_path / "a.json", tmp_path / "b.json"]
    system.write_replicas(paths, {"clinic_id": "C31", "cases": 7})
    rec = json.loads(paths[0].read_text())
    rec["payload"]["cases"] = 70
    paths[0].write_text(json.dumps(rec))
    assert ex.read_verified(paths)["cases"] == 7
    assert json.loads(paths[0].read_text())["payload"]["cases"] == 7  # repaired


def test_read_verified_fails_fast(tmp_path):
    paths = [tmp_path / "a.json", tmp_path / "b.json"]
    system.write_replicas(paths, {"cases": 7})
    for p in paths:
        p.write_text("garbage")
    with pytest.raises(ValueError):
        ex.read_verified(paths)


@pytest.mark.parametrize("user, action, district, expected", [
    (None, ("read", "S-COA"), "S-COA", False),
    ({"role": "clinic", "clinic_id": "C31"}, ("submit", "C31"), "S-COA", True),
    ({"role": "clinic", "clinic_id": "C31"}, ("submit", "C01"), "N-CEN", False),
    ({"role": "clinic", "clinic_id": "C31"}, ("read", "S-COA"), "S-COA", False),
    ({"role": "district_officer", "district_id": "S-COA"}, ("read", "S-COA"), "S-COA", True),
    ({"role": "district_officer", "district_id": "N-HIL"}, ("read", "S-COA"), "S-COA", False),
    ({"role": "admin"}, ("read", "S-COA"), "S-COA", False),
])
def test_authorize(user, action, district, expected):
    assert ex.authorize(user, action, district) is expected


def test_naive_parts_fail_the_bad_week():
    obs = bad_week.run_week(system.NaiveParts)
    assert obs["cholera_cases"] != obs["true_cases"]


def test_your_parts_survive_the_bad_week():
    obs = bad_week.run_week(ex)
    assert obs["cholera_cases"] == obs["true_cases"]
    assert obs["other_district_read"] == 403
    assert obs["forged_submit"] == 403
    assert obs["audit_entries"] == 8
