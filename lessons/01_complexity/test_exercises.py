import time

import pandas as pd
import pytest

from course.data import DISTRICTS, case_reports
from course.testing import load_exercises, load_module

ex = load_exercises(__file__)
v0 = load_module(__file__, "dashboard_v0")


@pytest.fixture(scope="module")
def csv_text():
    return case_reports().to_csv(index=False)


def test_load_reports_parses_dates(csv_text):
    df = ex.load_reports(csv_text)
    assert pd.api.types.is_datetime64_any_dtype(df["week_start"])
    assert df["cases"].dtype.kind == "i"


def test_new_date_format_needs_one_change(csv_text):
    df = ex.load_reports(csv_text)
    european = df.assign(week_start=df.week_start.dt.strftime("%d/%m/%Y")).to_csv(index=False)
    again = ex.load_reports(european, date_format="%d/%m/%Y")
    assert again["week_start"].equals(df["week_start"])


@pytest.mark.parametrize("disease", ["cholera", "measles", "malaria"])
def test_refactor_keeps_the_page_identical(csv_text, disease):
    incidence = ex.compute_incidence(ex.load_reports(csv_text), DISTRICTS, disease)
    assert ex.render_page(incidence, disease) == v0.build_page(csv_text, disease)


def test_cholera_alert_is_coastal(csv_text):
    inc = ex.compute_incidence(ex.load_reports(csv_text), DISTRICTS, "cholera")
    assert list(inc[inc.alert].district_id) == ["S-COA"]


def test_predict_quadratic():
    assert ex.predict_seconds(2.0, 4_000, 1_000_000, 2) == pytest.approx(125_000.0)


def test_predict_linear():
    assert ex.predict_seconds(0.5, 1_000, 3_000, 1) == pytest.approx(1.5)


def test_find_duplicates_small():
    df = pd.DataFrame({
        "report_id": [1, 2, 3, 4, 5],
        "clinic_id": ["C01", "C01", "C02", "C01", "C01"],
        "week_start": ["w1", "w1", "w1", "w2", "w1"],
        "disease": ["measles"] * 5,
    })
    assert ex.find_duplicate_reports(df) == [2, 5]


def test_find_duplicates_scales():
    base = case_reports(weeks=52)  # about 6,000 unique reports
    big = pd.concat([base] * 100, ignore_index=True)  # about 600,000 rows
    big["report_id"] = range(len(big))
    start = time.perf_counter()
    dups = ex.find_duplicate_reports(big)
    assert len(dups) == len(big) - len(base)
    assert time.perf_counter() - start < 5
