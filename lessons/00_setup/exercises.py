"""Module 0 exercises. Complete each TODO, then run: pytest lessons/00_setup"""

import pandas as pd


def incidence_per_100k(reports: pd.DataFrame, districts: pd.DataFrame, disease: str) -> pd.Series:
    """Total cases of ``disease`` per 100,000 people, indexed by district_id.

    Every district must appear, even if it reported no cases of the disease.
    """
    # TODO: filter to the disease, sum cases by district, divide by population.
    raise NotImplementedError


def invalid_district_reports(reports: pd.DataFrame, districts: pd.DataFrame) -> pd.DataFrame:
    """Rows of ``reports`` whose district_id is not one of the known districts."""
    # TODO
    raise NotImplementedError


def outbreak_district(reports: pd.DataFrame, disease: str) -> str:
    """The district_id whose weekly cases of ``disease`` grew the most from the
    first half of the reporting period to the second half (largest ratio)."""
    # TODO: hint, split the weeks in two, sum each half by district, compare.
    raise NotImplementedError
