import threading
import time

import pandas as pd
import pytest

from course.data import DISTRICTS, case_reports, clinics
from course.testing import load_exercises, load_module

ex = load_exercises(__file__)
PROFILE_OUTPUT = load_module(__file__, "exercises").PROFILE_OUTPUT


# Exercise 1 ----------------------------------------------------------------

def test_bottleneck_in_vaxrecords_profile():
    function, tottime = ex.bottleneck(PROFILE_OUTPUT)
    assert function == "{method 'execute' of 'sqlite3.Connection' objects}"
    assert tottime == pytest.approx(2.907)


def test_bottleneck_handles_recursive_ncalls():
    text = ("   ncalls  tottime  percall  cumtime  percall filename:lineno(function)\n"
            "        1    0.100    0.100    9.000    9.000 a.py:1(main)\n"
            "   500/10    4.250    0.008    8.000    0.800 a.py:9(walk)\n")
    assert ex.bottleneck(text) == ("a.py:9(walk)", 4.25)


# Exercise 2 ----------------------------------------------------------------

@pytest.fixture
def cache():
    return ex.IncidenceCache(case_reports(weeks=4), DISTRICTS)


def test_cache_computes_each_key_once(cache):
    first = cache.incidence("S-COA", "cholera")
    for _ in range(5):
        assert cache.incidence("S-COA", "cholera") == first
    cache.incidence("N-RIV", "measles")
    assert cache.computations == 2


def test_new_reports_appear(cache):
    before = cache.incidence("N-RIV", "cholera")
    cache.add_reports(pd.DataFrame({"district_id": ["N-RIV"], "disease": ["cholera"], "cases": [96]}))
    assert cache.incidence("N-RIV", "cholera") == pytest.approx(before + 100)  # 96 / 96,000 * 100k


def test_invalidation_is_targeted(cache):
    cache.incidence("N-RIV", "cholera")
    cache.incidence("S-COA", "measles")
    assert cache.computations == 2
    cache.add_reports(pd.DataFrame({"district_id": ["N-RIV"], "disease": ["cholera"], "cases": [5]}))
    cache.incidence("S-COA", "measles")          # untouched: still cached
    assert cache.computations == 2
    cache.incidence("N-RIV", "cholera")          # changed: recomputed once
    assert cache.computations == 3


# Exercise 3 ----------------------------------------------------------------

def test_people_inside():
    # 120 children an hour, each inside for 15 minutes: 2 per minute x 15 = 30.
    assert ex.people_inside(120, 15) == pytest.approx(30)


@pytest.mark.parametrize("per_hour, minutes, util, expected", [
    (90, 2.5, 0.8, 5),      # 3.75 busy -> 4.69 -> 5
    (120, 3, 0.8, 8),       # 6 busy -> 7.5 -> 8
    (120, 3, 1.0, 6),       # exactly 6 busy at 100%
    (300, 2, 0.75, 14),     # 10 busy -> 13.3 -> 14
])
def test_vaccinators_needed(per_hour, minutes, util, expected):
    assert ex.vaccinators_needed(per_hour, minutes, util) == expected


# Exercise 4 ----------------------------------------------------------------

def test_fetch_all_once_each_and_concurrently():
    calls, active, peak = [], [0], [0]
    lock = threading.Lock()

    def fake_fetch(clinic_id):
        with lock:
            calls.append(clinic_id)
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.01)
        with lock:
            active[0] -= 1
        return f"report from {clinic_id}"

    ids = list(clinics().clinic_id)
    result = ex.fetch_all(fake_fetch, ids, workers=8)
    assert result == {c: f"report from {c}" for c in ids}
    assert sorted(calls) == sorted(ids)          # exactly once each
    assert 1 < peak[0] <= 8                      # overlapped, but within the worker limit
