"""Module 6 worked answers."""

import math
from concurrent.futures import ThreadPoolExecutor

import pandas as pd


# Exercise 1 (PROFILE_OUTPUT is in exercises.py). The answer by eye: execute()
# has 2.9 of 3.9 seconds of tottime, and it is called 2,141 times: once per child. That is the "N+1 queries"
# pattern. The fix is batching: one query for all the district's doses, then
# group them in Python (or a JOIN). doses_for_child has the large cumtime, but
# almost none of it is its own: it is the caller, execute() is the cost.
def bottleneck(profile_text):
    lines = profile_text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().startswith("ncalls"))
    best = None
    for line in lines[start + 1:]:
        fields = line.split(maxsplit=5)
        if len(fields) < 6:
            continue
        tottime, function = float(fields[1]), fields[5]
        if best is None or tottime > best[1]:
            best = (function, tottime)
    return best


class IncidenceCache:
    def __init__(self, reports, districts):
        self.reports = reports[["district_id", "disease", "cases"]].copy()
        self.population = districts.set_index("district_id").population.to_dict()
        self.computations = 0
        self._cache = {}

    def _compute(self, district_id, disease):
        self.computations += 1
        mask = (self.reports.district_id == district_id) & (self.reports.disease == disease)
        return self.reports[mask].cases.sum() / self.population[district_id] * 100_000

    def incidence(self, district_id, disease):
        key = (district_id, disease)
        if key not in self._cache:
            self._cache[key] = self._compute(district_id, disease)
        return self._cache[key]

    def add_reports(self, new_reports):
        new = new_reports[["district_id", "disease", "cases"]]
        self.reports = pd.concat([self.reports, new], ignore_index=True)
        # Invalidate before anyone can read: never serve a value the new data changed.
        for key in set(zip(new.district_id, new.disease)):
            self._cache.pop(key, None)


def people_inside(arrivals_per_hour, minutes_inside):
    return arrivals_per_hour / 60 * minutes_inside


def vaccinators_needed(arrivals_per_hour, minutes_per_dose, max_utilisation=0.8):
    busy = people_inside(arrivals_per_hour, minutes_per_dose)   # average vaccinators busy
    return math.ceil(busy / max_utilisation - 1e-9)             # tolerate float round-off


def fetch_all(fetch, clinic_ids, workers=8):
    clinic_ids = list(clinic_ids)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return dict(zip(clinic_ids, pool.map(fetch, clinic_ids)))
