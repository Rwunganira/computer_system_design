from datetime import date

import pandas as pd
import pytest

from course.data import case_reports, clinics, population
from course.testing import load_exercises, load_module

ex = load_exercises(__file__)
pr = load_module(__file__, "patient_resolver")


@pytest.fixture(scope="module")
def reports():
    return case_reports()


@pytest.fixture(scope="module")
def client(reports):
    return ex.create_district_app(reports).test_client()


def total(reports, district_id):
    return int(reports[reports.district_id == district_id].cases.sum())


# --- Exercise 1: resolving district names ---------------------------------------------------

def test_unique_name_resolves():
    assert ex.resolve_district("Riverside") == "N-RIV"


def test_district_id_is_already_a_name():
    assert ex.resolve_district("N-CEN") == "N-CEN"


def test_central_is_ambiguous():
    with pytest.raises(ex.AmbiguousName) as info:
        ex.resolve_district("Central")
    assert info.value.candidates == ["N-CEN", "S-CEN"]


def test_region_qualifies_the_name():
    assert ex.resolve_district("Central", region="North") == "N-CEN"
    assert ex.resolve_district("Central", region="South") == "S-CEN"


def test_unknown_names():
    with pytest.raises(LookupError):
        ex.resolve_district("Atlantis")
    with pytest.raises(LookupError):
        ex.resolve_district("Riverside", region="South")  # exists, but not in that context


def test_existing_url_still_works(client, reports):
    resp = client.get("/districts/Riverside/cases")
    assert resp.status_code == 200
    assert resp.get_json() == {"district_id": "N-RIV", "cases": total(reports, "N-RIV")}


def test_ambiguous_url_offers_choices(client):
    resp = client.get("/districts/Central/cases")
    assert resp.status_code == 300
    assert resp.get_json()["candidates"] == ["/districts/N-CEN/cases", "/districts/S-CEN/cases"]


def test_every_district_is_reachable(client, reports):
    for district_id in ["N-CEN", "S-CEN"]:
        resp = client.get(f"/districts/{district_id}/cases")
        assert resp.get_json() == {"district_id": district_id, "cases": total(reports, district_id)}
    resp = client.get("/regions/North/districts/Central/cases")
    assert resp.status_code == 200
    assert resp.get_json()["district_id"] == "N-CEN"


def test_unknown_url_is_404(client):
    assert client.get("/districts/Atlantis/cases").status_code == 404
    assert client.get("/regions/East/districts/Central/cases").status_code == 404


def test_naive_example_app_really_loses_north_central(reports):
    # The bug Exercise 1 fixes: the example's name table has 7 entries for 8 districts.
    app = pr.create_app(reports)
    assert app.test_client().get("/districts/Central/cases").get_json()["district_id"] == "S-CEN"
    assert "N-CEN" not in app.config["by_name"].values()


# --- Exercise 2: aliases for renamed clinics ----------------------------------------------

@pytest.fixture
def names():
    # Careful: clinic names collide too. Both Central districts have a "Central Health
    # Centre 1", so this dict keeps 35 of the 40 clinics. These tests avoid those names.
    clinic_ids = dict(zip(clinics().clinic_name, clinics().clinic_id))
    return clinic_ids, {}


def test_current_name_resolves(names):
    clinic_ids, aliases = names
    assert ex.resolve_clinic("Coastal Health Centre 3", clinic_ids, aliases) == "C33"


def test_old_names_still_resolve_after_renames(names):
    clinic_ids, aliases = names
    before = len(clinic_ids)
    ex.rename_clinic(clinic_ids, aliases, "Coastal Health Centre 3", "Coastal District Hospital")
    ex.rename_clinic(clinic_ids, aliases, "Coastal District Hospital", "Coastal Regional Hospital")
    for name in ["Coastal Health Centre 3", "Coastal District Hospital", "Coastal Regional Hospital"]:
        assert ex.resolve_clinic(name, clinic_ids, aliases) == "C33"
    assert "Coastal Health Centre 3" not in clinic_ids
    assert len(clinic_ids) == before


def test_rename_refuses_bad_requests(names):
    clinic_ids, aliases = names
    with pytest.raises(LookupError):
        ex.rename_clinic(clinic_ids, aliases, "No Such Clinic", "Anything")
    with pytest.raises(ValueError):
        ex.rename_clinic(clinic_ids, aliases, "Savanna Health Centre 1", "Savanna Health Centre 2")


def test_unknown_clinic_and_alias_loop(names):
    clinic_ids, _ = names
    with pytest.raises(LookupError):
        ex.resolve_clinic("No Such Clinic", clinic_ids, {})
    loop = {"Old A": "Old B", "Old B": "Old A"}
    with pytest.raises(LookupError):
        ex.resolve_clinic("Old A", clinic_ids, loop)


# --- Exercise 3: conflicting birth dates -----------------------------------------------------

def test_conflicting_birth_dates():
    records = pd.DataFrame([
        ("R1", date(2022, 1, 5), "clinic_a"),
        ("R1", date(2022, 1, 5), "clinic_b"),   # same child seen twice: fine
        ("R2", date(2023, 3, 1), "clinic_a"),
        ("R2", date(2021, 7, 9), "clinic_c"),   # conflict
        ("R3", date(2024, 2, 2), "clinic_b"),
    ], columns=["registry_id", "birth_date", "clinic"])
    assert ex.conflicting_birth_dates(records) == ["R2"]


def test_finds_children_merged_by_an_overloaded_name():
    # Bind each child to a "registry ID" made from given name + family name: an overloaded
    # name that merges many different children. Every merged ID with two birth dates is found.
    people = population()
    records = pd.DataFrame({
        "registry_id": people.given_name + " " + people.family_name,
        "birth_date": people.birth_date,
        "clinic": "clinic_a",
    })
    found = ex.conflicting_birth_dates(records)
    expected = sorted(n for n, g in records.groupby("registry_id") if g.birth_date.nunique() > 1)
    assert found == expected and len(found) > 100


def test_no_conflicts_in_a_clean_registry():
    people = population(200)
    records = pd.DataFrame({"registry_id": people.person_id, "birth_date": people.birth_date, "clinic": "x"})
    assert ex.conflicting_birth_dates(records) == []
