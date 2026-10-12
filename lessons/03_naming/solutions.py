"""Module 3 worked answers."""

from flask import Flask, jsonify

from course.data import DISTRICTS
from course.testing import load_module

# Reuse the exercise file's exception class so tests can catch it either way.
AmbiguousName = load_module(__file__, "exercises").AmbiguousName


def resolve_district(name, region=None, districts=DISTRICTS):
    if name in set(districts.district_id):
        return name
    found = districts[districts.district_name == name]
    if region is not None:
        found = found[found.region == region]
    ids = sorted(found.district_id)
    if not ids:
        raise LookupError(f"no district named {name!r}" + (f" in {region}" if region else ""))
    if len(ids) > 1:
        raise AmbiguousName(name, ids)
    return ids[0]


def create_district_app(reports, districts=DISTRICTS):
    totals = reports.groupby("district_id").cases.sum()
    app = Flask(__name__)

    def answer(name, region=None):
        try:
            district_id = resolve_district(name, region, districts)
        except AmbiguousName as err:
            return jsonify(candidates=[f"/districts/{d}/cases" for d in err.candidates]), 300
        except LookupError as err:
            return jsonify(error=str(err)), 404
        return jsonify(district_id=district_id, cases=int(totals.get(district_id, 0)))

    @app.get("/districts/<name>/cases")
    def district_cases(name):
        return answer(name)

    @app.get("/regions/<region>/districts/<name>/cases")
    def regional_district_cases(region, name):
        return answer(name, region)

    return app


def resolve_clinic(name, clinic_ids, aliases, max_hops=10):
    for _ in range(max_hops + 1):
        if name in clinic_ids:
            return clinic_ids[name]
        if name not in aliases:
            raise LookupError(f"no clinic named {name!r}")
        name = aliases[name]
    raise LookupError(f"alias chain too long (loop?) at {name!r}")


def rename_clinic(clinic_ids, aliases, old, new):
    if old not in clinic_ids:
        raise LookupError(f"no current clinic named {old!r}")
    if new in clinic_ids or new in aliases:
        raise ValueError(f"{new!r} is already in use")
    clinic_ids[new] = clinic_ids.pop(old)
    aliases[old] = new


def conflicting_birth_dates(records):
    counts = records.groupby("registry_id").birth_date.nunique()
    return sorted(counts[counts > 1].index)
