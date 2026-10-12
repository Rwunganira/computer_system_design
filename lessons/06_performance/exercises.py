"""Module 6 exercises. Complete each TODO, then run: pytest lessons/06_performance"""

# ---------------------------------------------------------------------------
# Exercise 1. Find the bottleneck.
#
# This is cProfile output (sorted by cumtime) from the VaxRecords endpoint that
# lists every child in a district with their doses. Before writing any code,
# read it and decide: which line is the bottleneck, and what would you change?
# Then write a function that finds it for you.
# ---------------------------------------------------------------------------

PROFILE_OUTPUT = """\
         412958 function calls (409311 primitive calls) in 3.912 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.002    0.002    3.912    3.912 app.py:88(district_children)
        1    0.031    0.031    3.874    3.874 vax_records.py:52(children_with_doses)
     2140    0.019    0.000    3.611    0.002 vax_records.py:31(doses_for_child)
     2141    2.907    0.001    2.907    0.001 {method 'execute' of 'sqlite3.Connection' objects}
     2140    0.412    0.000    0.598    0.000 {method 'fetchall' of 'sqlite3.Cursor' objects}
  2140/12    0.071    0.000    0.205    0.017 vax_records.py:19(format_dose)
    14980    0.104    0.000    0.104    0.000 {built-in method builtins.isinstance}
        1    0.008    0.008    0.036    0.036 json/encoder.py:183(encode)
"""


def bottleneck(profile_text):
    """Return (function, tottime) for the row with the largest tottime.

    ``function`` is the last column exactly as printed, for example
    "vax_records.py:31(doses_for_child)". ``tottime`` is a float. Rows may
    have ncalls like "2140/12" (recursive calls). Ignore lines that are not
    rows of the table.
    """
    # TODO: find the header line, then split each later row into 6 fields.
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 2. Cache invalidation.
#
# dashboard_fixes.py caches incidence with lru_cache, so a new report never
# shows up. Fix it with a cache you control. When reports arrive, forget only
# the entries they change: a new cholera report from Riverside must not throw
# away the cached measles figure for Coastal.
# ---------------------------------------------------------------------------

class IncidenceCache:
    """Incidence per 100,000 for (district_id, disease), computed at most once
    until a new report for that district and disease arrives."""

    def __init__(self, reports, districts):
        self.reports = reports[["district_id", "disease", "cases"]].copy()
        self.population = districts.set_index("district_id").population.to_dict()
        self.computations = 0      # how many times _compute ran (tests check this)
        self._cache = {}           # (district_id, disease) -> incidence

    def _compute(self, district_id, disease):
        """The expensive part. Do not change it."""
        self.computations += 1
        mask = (self.reports.district_id == district_id) & (self.reports.disease == disease)
        return self.reports[mask].cases.sum() / self.population[district_id] * 100_000

    def incidence(self, district_id, disease):
        """Return the cached value, computing it only on a miss."""
        # TODO
        raise NotImplementedError

    def add_reports(self, new_reports):
        """Append ``new_reports`` (a DataFrame with district_id, disease, cases)
        and invalidate exactly the cache entries they affect."""
        # TODO
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 3. Little's law for a mass vaccination day.
# ---------------------------------------------------------------------------

def people_inside(arrivals_per_hour, minutes_inside):
    """Average number of people in the clinic (Little's law: N = X x R).

    Watch the units: arrivals are per hour, time inside is in minutes.
    """
    # TODO
    raise NotImplementedError


def vaccinators_needed(arrivals_per_hour, minutes_per_dose, max_utilisation=0.8):
    """Fewest vaccinators so that each is busy at most ``max_utilisation`` of the time.

    Hint: apply Little's law to the vaccinators alone. A child "inside" a
    vaccinator stays ``minutes_per_dose``; so on average how many vaccinators
    are busy?
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 4. Concurrency.
# ---------------------------------------------------------------------------

def fetch_all(fetch, clinic_ids, workers=8):
    """Call ``fetch(clinic_id)`` for every clinic, up to ``workers`` at a time.

    Return a dict {clinic_id: result}. Call ``fetch`` exactly once per clinic.
    """
    # TODO: use concurrent.futures.ThreadPoolExecutor.
    raise NotImplementedError
