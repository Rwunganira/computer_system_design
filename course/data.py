"""Synthetic data for the course. No real patients, clinics or places.

Everything is generated from a seed, so the same call always returns the same
data. That makes examples repeatable and tests stable.

    from course.data import case_reports, population, vaccinations
    reports = case_reports()          # weekly case counts from 40 clinics
    people = population(2_000)        # a synthetic population
    doses = vaccinations(people)      # doses given to those people

Run ``python -m course.data`` to write the datasets as CSV files to
``data/generated/`` and print a summary.
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Two regions, each with four districts. Both regions have a district named
# "Central": names are not unique, which Module 3 (Naming) deals with.
DISTRICTS = pd.DataFrame(
    [
        ("N-CEN", "Central", "North", 182_000),
        ("N-RIV", "Riverside", "North", 96_000),
        ("N-HIL", "Hillview", "North", 74_000),
        ("N-LAK", "Lakeshore", "North", 121_000),
        ("S-CEN", "Central", "South", 205_000),
        ("S-SAV", "Savanna", "South", 88_000),
        ("S-COA", "Coastal", "South", 143_000),
        ("S-HIG", "Highlands", "South", 67_000),
    ],
    columns=["district_id", "district_name", "region", "population"],
)

DISEASES = ["measles", "cholera", "malaria"]
VACCINES = ["BCG", "OPV1", "OPV2", "DTP1", "DTP2", "MCV1", "MCV2"]

_GIVEN = ["Amina", "Jean", "Grace", "Eric", "Aline", "Patrick", "Diane", "Yves",
          "Clarisse", "Moses", "Ruth", "David", "Esther", "Joseph", "Nadia", "Paul"]
_FAMILY = ["Uwase", "Habimana", "Mukamana", "Niyonzima", "Ingabire", "Mugisha",
           "Uwimana", "Nshimiyimana", "Iradukunda", "Hakizimana", "Mutesi", "Kamanzi"]

# Weekly cases per 100,000 people, a rough baseline for each disease.
_BASE_RATE = {"measles": 0.8, "cholera": 1.5, "malaria": 40.0}


def clinics():
    """Five clinics per district, 40 in all: clinic_id, clinic_name, district_id."""
    rows = []
    n = 1
    for district_id, district_name in zip(DISTRICTS.district_id, DISTRICTS.district_name):
        for k in range(1, 6):
            rows.append((f"C{n:02d}", f"{district_name} Health Centre {k}", district_id))
            n += 1
    return pd.DataFrame(rows, columns=["clinic_id", "clinic_name", "district_id"])


def case_reports(weeks=12, start=date(2026, 1, 5), seed=42, outbreak=("S-COA", "cholera", 6)):
    """Weekly case counts: one row per clinic, week and disease.

    ``outbreak`` is (district_id, disease, first_week_index): from that week on,
    cases of that disease in that district rise sharply, so there is something
    for the dashboard to flag. Pass ``outbreak=None`` for a quiet season.
    """
    rng = random.Random(seed)
    cl = clinics().merge(DISTRICTS, on="district_id")
    rows = []
    report_id = 1
    for w in range(weeks):
        week_start = start + timedelta(weeks=w)
        for c in cl.itertuples():
            catchment = c.population / 5
            for disease in DISEASES:
                expected = _BASE_RATE[disease] * catchment / 100_000
                if outbreak and c.district_id == outbreak[0] and disease == outbreak[1] and w >= outbreak[2]:
                    expected *= 8 * (w - outbreak[2] + 1)
                cases = _poisson(rng, expected)
                rows.append((report_id, c.clinic_id, c.district_id, week_start, disease, cases))
                report_id += 1
    return pd.DataFrame(rows, columns=["report_id", "clinic_id", "district_id", "week_start", "disease", "cases"])


def population(n=2_000, seed=7):
    """A synthetic population: person_id, given_name, family_name, birth_date, sex, district_id."""
    rng = random.Random(seed)
    districts = list(DISTRICTS.district_id)
    weights = list(DISTRICTS.population)
    rows = []
    for i in range(1, n + 1):
        birth = date(2021, 1, 1) + timedelta(days=rng.randrange(5 * 365))
        rows.append((
            f"P{i:06d}",
            rng.choice(_GIVEN),
            rng.choice(_FAMILY),
            birth,
            rng.choice("FM"),
            rng.choices(districts, weights)[0],
        ))
    return pd.DataFrame(rows, columns=["person_id", "given_name", "family_name", "birth_date", "sex", "district_id"])


def vaccinations(people=None, seed=11, coverage=0.85):
    """Doses given: dose_id, person_id, vaccine, dose_date, clinic_id.

    Each child receives each vaccine with probability ``coverage``, at a clinic
    in their own district, on a date after their birth.
    """
    if people is None:
        people = population()
    rng = random.Random(seed)
    cl = clinics()
    by_district = cl.groupby("district_id").clinic_id.apply(list).to_dict()
    schedule_days = {"BCG": 0, "OPV1": 42, "OPV2": 70, "DTP1": 42, "DTP2": 70, "MCV1": 270, "MCV2": 450}
    rows = []
    dose_id = 1
    for p in people.itertuples():
        for vaccine in VACCINES:
            if rng.random() < coverage:
                when = p.birth_date + timedelta(days=schedule_days[vaccine] + rng.randrange(30))
                rows.append((dose_id, p.person_id, vaccine, when, rng.choice(by_district[p.district_id])))
                dose_id += 1
    return pd.DataFrame(rows, columns=["dose_id", "person_id", "vaccine", "dose_date", "clinic_id"])


def write_all(out_dir=Path(__file__).resolve().parent.parent / "data" / "generated"):
    """Write every dataset as CSV to ``out_dir`` and return the paths written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    people = population()
    tables = {
        "districts": DISTRICTS,
        "clinics": clinics(),
        "case_reports": case_reports(),
        "population": people,
        "vaccinations": vaccinations(people),
    }
    paths = []
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        paths.append(path)
    return paths


def _poisson(rng, lam):
    """Draw from a Poisson distribution (the standard library has none)."""
    if lam > 30:  # normal approximation is fine for large counts
        return max(0, round(rng.gauss(lam, lam ** 0.5)))
    # Knuth's method
    limit, k, p = 2.718281828459045 ** -lam, 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


if __name__ == "__main__":
    for path in write_all():
        df = pd.read_csv(path)
        print(f"{path.name:<18} {len(df):>7,} rows  columns: {', '.join(df.columns)}")
