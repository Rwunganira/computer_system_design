import pytest

from course.data import DISTRICTS, case_reports
from course.testing import load_exercises

ex = load_exercises(__file__)  # also puts this lesson folder on sys.path

import checksummed_store  # noqa: E402  (the lesson's example modules)
import tmr_incidence  # noqa: E402


@pytest.fixture(scope="module")
def reports():
    return case_reports()


# Exercise 1

def test_checked_incidence_matches_on_good_input(reports):
    assert ex.checked_incidence(reports, DISTRICTS, "cholera") == tmr_incidence.incidence(reports, DISTRICTS, "cholera")


def test_rejects_negative_cases(reports):
    bad = reports.copy()
    bad.loc[bad.report_id == 17, "cases"] = -3
    with pytest.raises(ValueError, match="17"):
        ex.checked_incidence(bad, DISTRICTS, "cholera")


def test_rejects_missing_cases(reports):
    bad = reports.astype({"cases": float})
    bad.loc[bad.report_id == 23, "cases"] = float("nan")
    with pytest.raises(ValueError, match="23"):
        ex.checked_incidence(bad, DISTRICTS, "measles")


def test_rejects_zero_population(reports):
    bad = DISTRICTS.copy()
    bad.loc[bad.district_id == "S-HIG", "population"] = 0
    with pytest.raises(ValueError, match="S-HIG"):
        ex.checked_incidence(reports, bad, "malaria")


# Exercise 2

@pytest.mark.parametrize("r", [0.0, 0.3, 0.5, 0.9, 0.99, 1.0])
def test_tmr_reliability_formula(r):
    assert ex.tmr_reliability(r) == pytest.approx(3 * r**2 - 2 * r**3)


def test_break_even():
    r = ex.tmr_break_even()
    assert 0 < r < 1
    assert ex.tmr_reliability(r) == pytest.approx(r)
    assert ex.tmr_reliability(r - 0.1) < r - 0.1   # worse than one replica below it
    assert ex.tmr_reliability(r + 0.1) > r + 0.1   # better above it


@pytest.mark.parametrize("r", [0.3, 0.9])
def test_simulation_agrees_with_formula(r):
    assert ex.simulate_tmr(r, trials=20_000, seed=1) == pytest.approx(ex.tmr_reliability(r), abs=0.02)
    assert ex.simulate_tmr(r, trials=500, seed=5) == ex.simulate_tmr(r, trials=500, seed=5)


# Exercise 3

DATA = b"week_start,cases\n2026-01-05,3\n2026-01-12,4\n"


@pytest.fixture
def replicas(tmp_path):
    folders = [tmp_path / "a", tmp_path / "b", tmp_path / "c"]
    for f in folders:
        checksummed_store.save(f, "cholera.csv", DATA)
    return folders


def test_reads_good_copy_and_repairs_corrupted(replicas):
    checksummed_store.flip_bit(replicas[0] / "cholera.csv", 20)
    assert ex.read_with_repair(replicas, "cholera.csv") == DATA
    for f in replicas:
        assert checksummed_store.load(f, "cholera.csv") == DATA


def test_repairs_missing_replica(replicas):
    (replicas[1] / "cholera.csv").unlink()
    (replicas[2] / "cholera.csv.sha256").unlink()
    assert ex.read_with_repair(replicas, "cholera.csv") == DATA
    for f in replicas:
        assert checksummed_store.load(f, "cholera.csv") == DATA


def test_all_corrupted_raises(replicas):
    for f in replicas:
        checksummed_store.flip_bit(f / "cholera.csv", 20)
    with pytest.raises(checksummed_store.CorruptionError):
        ex.read_with_repair(replicas, "cholera.csv")
