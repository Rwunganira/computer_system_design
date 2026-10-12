"""Naming patients and districts: contexts, resolution, overloaded names and indirection.

Each clinic numbers its own patients, so "P-0042" means different children at different
clinics. A name only means something in a context. This example builds contexts as
dictionaries, resolves path names through them to a national registry, shows what goes wrong
when a name is overloaded with meaning, and maps Flask URLs onto names.
"""

from datetime import date

from flask import Flask, jsonify

from course.data import DISTRICTS, case_reports, population, vaccinations

CLINICS = ["clinic_a", "clinic_b", "clinic_c"]


def build_registry(people):
    """The national registry: a context binding registry IDs to patient records."""
    return {row["person_id"]: row for row in people.to_dict("records")}


def build_clinic_contexts(people, per_clinic=200):
    """Each clinic's context binds its own local IDs (P-0001, P-0002, ...) to registry IDs."""
    contexts = {}
    for k, clinic in enumerate(CLINICS):
        ids = people.person_id.iloc[k * per_clinic:(k + 1) * per_clinic]
        contexts[clinic] = {f"P-{i:04d}": rid for i, rid in enumerate(ids, start=1)}
    return contexts


def resolve(name, context):
    """Resolve a path name such as 'clinic_a/P-0042' one component at a time.

    Each lookup's value is the context for the next component. Raises LookupError when a
    component has no binding.
    """
    value = context
    for part in name.strip("/").split("/"):
        if not isinstance(value, dict) or part not in value:
            raise LookupError(f"{name!r}: no binding for {part!r}")
        value = value[part]
    return value


def create_app(reports):
    """A Flask app whose URLs name districts by their human-readable name."""
    # The naive name -> id table. "Central" is bound twice; the dict keeps the last binding.
    by_name = {row.district_name: row.district_id for row in DISTRICTS.itertuples()}
    totals = reports.groupby("district_id").cases.sum()
    app = Flask(__name__)

    @app.get("/districts/<name>/cases")
    def district_cases(name):
        if name not in by_name:
            return jsonify(error=f"no district named {name!r}"), 404
        district_id = by_name[name]
        return jsonify(district=name, district_id=district_id, cases=int(totals[district_id]))

    app.config["by_name"] = by_name
    return app


def main():
    people = population()
    registry = build_registry(people)
    clinics = build_clinic_contexts(people)
    root = {**clinics, "registry": registry}  # the root context: every top-level name

    print("1. The same local name in two contexts names two different children:")
    for path in ["clinic_a/P-0042", "clinic_b/P-0042"]:
        rid = resolve(path, root)
        child = resolve(f"registry/{rid}", root)
        print(f"   {path:<16} -> {rid} -> {child['given_name']} {child['family_name']}, born {child['birth_date']}")
    print("   Relative name 'P-0042' with working context clinic_c ->", resolve("P-0042", clinics["clinic_c"]))
    try:
        resolve("clinic_a/P-9999", root)
    except LookupError as err:
        print(f"   Unbound name: {err}")

    print("\n2. An overloaded name: identifying children by name + date of birth")
    key = lambda r: f"{r['given_name']} {r['family_name']} {r['birth_date']}"
    by_key = {key(r): rid for rid, r in registry.items()}  # later bindings overwrite earlier ones
    print(f"   {len(registry):,} children but only {len(by_key):,} distinct keys")
    doses = vaccinations(people)
    seen = {}
    for rid, record in registry.items():
        if key(record) in seen:
            first = seen[key(record)]
            merged = doses[doses.person_id.isin([first, rid])].sort_values("vaccine")
            print(f"   '{key(record)}' is both {first} and {rid}; the key resolves only to {by_key[key(record)]}")
            print(f"   merged, one child appears to have had vaccines twice: {', '.join(merged.vaccine)}")
        seen.setdefault(key(record), rid)

    print("\n3. Indirection: clinics bind local names to registry IDs, not to copies of the record")
    rid = resolve("clinic_a/P-0007", root)
    clinics["clinic_b"]["P-0201"] = rid  # the child moves; clinic_b binds its own new name
    print(f"   Birth date was mistyped as {registry[rid]['birth_date']}; corrected once, in the registry:")
    registry[rid] = {**registry[rid], "birth_date": date(2022, 11, 2)}
    for path in ["clinic_a/P-0007", "clinic_b/P-0201"]:  # every name that leads here sees the fix
        target = resolve(path, root)
        print(f"   {path:<16} -> {target} -> born {resolve('registry/' + target, root)['birth_date']}")

    print("\n4. URLs are names too: /districts/<name>/cases")
    app = create_app(case_reports())
    print(f"   {len(DISTRICTS)} districts, but the name table has {len(app.config['by_name'])} entries")
    client = app.test_client()  # calls the app in-process; no server or port needed
    for name in ["Riverside", "Central", "Atlantis"]:
        resp = client.get(f"/districts/{name}/cases")
        print(f"   GET /districts/{name}/cases -> {resp.status_code} {resp.get_json()}")
    print("   North Central (N-CEN, 182,000 people) cannot be reached by any URL.")


if __name__ == "__main__":
    main()
