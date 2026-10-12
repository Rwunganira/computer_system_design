"""Module 8 worked answers."""

import random

import checksummed_store
import tmr_incidence


def checked_incidence(reports, districts, disease):
    bad = reports[reports.cases.isna() | (reports.cases < 0)]
    if len(bad):
        raise ValueError(f"impossible case counts in report_id(s) {list(bad.report_id)}")
    empty = districts[districts.population <= 0]
    if len(empty):
        raise ValueError(f"population <= 0 in district_id(s) {list(empty.district_id)}")
    return tmr_incidence.incidence(reports, districts, disease)


def tmr_reliability(r):
    return r**3 + 3 * r**2 * (1 - r)  # = 3r^2 - 2r^3


def tmr_break_even():
    # 3r^2 - 2r^3 = r  ->  2r^2 - 3r + 1 = 0  ->  (2r - 1)(r - 1) = 0
    return 0.5


def simulate_tmr(r, trials=20_000, seed=0):
    rng = random.Random(seed)
    ok = sum(sum(rng.random() < r for _ in range(3)) >= 2 for _ in range(trials))
    return ok / trials


def read_with_repair(folders, name):
    good, bad = None, []
    for folder in folders:
        try:
            data = checksummed_store.load(folder, name)
        except (checksummed_store.CorruptionError, FileNotFoundError):
            bad.append(folder)
            continue
        if good is None:
            good = data
    if good is None:
        raise checksummed_store.CorruptionError(f"no good replica of {name}")
    for folder in bad:
        checksummed_store.save(folder, name, good)
    return good
