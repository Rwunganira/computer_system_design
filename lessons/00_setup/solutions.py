"""Module 0 worked answers."""

import pandas as pd


def incidence_per_100k(reports, districts, disease):
    cases = reports[reports.disease == disease].groupby("district_id").cases.sum()
    pop = districts.set_index("district_id").population
    return (cases.reindex(pop.index, fill_value=0) / pop * 100_000).rename("incidence")


def invalid_district_reports(reports, districts):
    return reports[~reports.district_id.isin(districts.district_id)]


def outbreak_district(reports, disease):
    df = reports[reports.disease == disease]
    weeks = sorted(df.week_start.unique())
    half = len(weeks) // 2
    first = df[df.week_start.isin(weeks[:half])].groupby("district_id").cases.sum()
    second = df[df.week_start.isin(weeks[half:])].groupby("district_id").cases.sum()
    ratio = (second + 1) / (first + 1)  # +1 so a district with zero early cases does not divide by zero
    return ratio.idxmax()
