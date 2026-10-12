import pandas as pd
import pytest

from course.data import DISTRICTS, case_reports
from course.testing import load_exercises

ex = load_exercises(__file__)


@pytest.fixture(scope="module")
def reports():
    return case_reports()


def test_incidence_covers_every_district(reports):
    inc = ex.incidence_per_100k(reports, DISTRICTS, "measles")
    assert set(inc.index) == set(DISTRICTS.district_id)


def test_incidence_value(reports):
    inc = ex.incidence_per_100k(reports, DISTRICTS, "malaria")
    expected = reports[(reports.disease == "malaria") & (reports.district_id == "N-CEN")].cases.sum() / 182_000 * 100_000
    assert inc["N-CEN"] == pytest.approx(expected)


def test_district_with_no_cases_is_zero():
    one = pd.DataFrame({"district_id": ["N-CEN"], "disease": ["measles"], "cases": [3]})
    inc = ex.incidence_per_100k(one, DISTRICTS, "measles")
    assert inc["S-HIG"] == 0


def test_invalid_districts(reports):
    bad = pd.concat([reports.head(3), pd.DataFrame({"district_id": ["XX-999"], "cases": [1]})])
    found = ex.invalid_district_reports(bad, DISTRICTS)
    assert list(found.district_id) == ["XX-999"]


def test_finds_the_cholera_outbreak(reports):
    assert ex.outbreak_district(reports, "cholera") == "S-COA"
