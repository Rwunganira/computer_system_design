"""Module 1 exercises. Complete each TODO, then run: pytest lessons/01_complexity"""

import pandas as pd


# Exercise 1: propagation of effects.
# dashboard_v0.build_page() parses dates in several places. Clinics in one region
# now upload dates as day/month/year ("23/03/2026"). Instead of patching every
# place, give the date format exactly one home.

def load_reports(csv_text: str, date_format: str = "%Y-%m-%d") -> pd.DataFrame:
    """Parse uploaded CSV into a DataFrame with week_start as datetime64 and cases as int.

    This must be the ONLY function in your design that knows the date format.
    """
    # TODO: hint, pd.read_csv(io.StringIO(csv_text)) then pd.to_datetime(..., format=date_format)
    raise NotImplementedError


# Exercise 2: modularity. Split dashboard_v0.build_page into three modules with
# narrow interfaces. Together they must produce exactly the same page.

def compute_incidence(reports: pd.DataFrame, districts: pd.DataFrame, disease: str, weeks: int = 4) -> pd.DataFrame:
    """Cases and incidence per 100,000 for the last ``weeks`` weeks of ``disease``.

    Returns one row per district, in the order of ``districts``, with columns
    district_id, district_name, region, cases, rate, alert (rate > 10).
    Also store the latest week as ``result.attrs["latest"]`` (a Timestamp).
    """
    # TODO
    raise NotImplementedError


def render_page(incidence: pd.DataFrame, disease: str) -> str:
    """HTML identical to dashboard_v0.build_page's output, built only from ``incidence``."""
    # TODO
    raise NotImplementedError


# Exercise 3: incommensurate scaling. scaling.py measured the naive duplicate check.

def predict_seconds(measured_seconds: float, measured_n: int, target_n: int, exponent: float) -> float:
    """Predict the running time at ``target_n`` for an algorithm whose time grows as n**exponent."""
    # TODO
    raise NotImplementedError


def find_duplicate_reports(reports: pd.DataFrame) -> list:
    """report_ids of reports that repeat an earlier report's (clinic_id, week_start, disease).

    The first occurrence is not a duplicate; later ones are. Must handle a
    million rows in a few seconds, so no comparing every pair.
    """
    # TODO
    raise NotImplementedError
