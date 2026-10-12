import copy

import pytest

from course.testing import load_exercises

ex = load_exercises(__file__)  # also puts this folder on sys.path, so the next import works
import vax_api_insecure  # noqa: E402

N_CEN_CHILD, S_COA_CHILD = "P000001", "P000002"  # districts N-CEN and S-COA


def _login(client, username):
    password = vax_api_insecure.USERS[username]["password"]  # synthetic test password
    r = client.post("/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


# --- 1. The record-access bug ------------------------------------------------

def test_original_app_has_the_bug():
    """The test that would have caught it, run against the original app."""
    client = vax_api_insecure.create_app().test_client()
    amina = _login(client, "amina")  # North-Central officer
    assert client.get(f"/patients/{S_COA_CHILD}", headers=amina).status_code == 200  # leak!


@pytest.fixture
def client():
    return ex.create_app().test_client()


def test_officer_reads_own_district(client):
    r = client.get(f"/patients/{N_CEN_CHILD}", headers=_login(client, "amina"))
    assert r.status_code == 200
    assert r.get_json()["district_id"] == "N-CEN"


def test_officer_cannot_read_other_district(client):
    assert client.get(f"/patients/{S_COA_CHILD}", headers=_login(client, "amina")).status_code == 403
    assert client.get(f"/patients/{N_CEN_CHILD}", headers=_login(client, "eric")).status_code == 403


def test_national_reads_everything(client):
    ruth = _login(client, "ruth")
    for pid in (N_CEN_CHILD, S_COA_CHILD):
        assert client.get(f"/patients/{pid}", headers=ruth).status_code == 200


def test_not_logged_in(client):
    assert client.get(f"/patients/{N_CEN_CHILD}").status_code == 401


def test_fail_safe_defaults():
    patient = {"district_id": "N-CEN"}
    assert ex.can_read({"role": "auditor", "district": "N-CEN"}, patient) is False
    assert ex.can_read({"role": "district_officer"}, patient) is False
    assert ex.can_read({}, patient) is False


# --- 2. Hash-chained audit log -----------------------------------------------

def _log():
    log = []
    for i in range(1, 5):
        ex.append_entry(log, {"user": "amina", "action": "read", "record": f"P{i:06d}"})
    return log


def test_chain_links():
    log = _log()
    assert log[0]["prev"] == ex.GENESIS
    assert all(b["prev"] == a["hash"] for a, b in zip(log, log[1:]))
    assert ex.verify_chain(log)
    assert ex.verify_chain(log, head=log[-1]["hash"])


def test_append_returns_new_head():
    log = _log()
    h = ex.append_entry(log, {"user": "ruth", "action": "read", "record": "P000009"})
    assert h == log[-1]["hash"] and len(log) == 5


def test_edit_is_detected_even_if_hash_recomputed():
    log = _log()
    log[1]["entry"]["record"] = "P000099"
    assert not ex.verify_chain(copy.deepcopy(log))
    # A smarter attacker recomputes that entry's hash; the next link still breaks.
    log[1]["hash"] = ex.entry_hash(log[1]["prev"], log[1]["entry"])
    assert not ex.verify_chain(log)


def test_delete_and_reorder_are_detected():
    log = _log()
    assert not ex.verify_chain(log[:1] + log[2:])
    assert not ex.verify_chain([log[1], log[0]] + log[2:])


def test_truncation_needs_the_head():
    log = _log()
    head = log[-1]["hash"]
    assert ex.verify_chain(log[:-1])  # cutting off the end looks fine on its own...
    assert not ex.verify_chain(log[:-1], head=head)  # ...but not against the saved head


# --- 3. Threat model ----------------------------------------------------------

def test_threat_model_shape():
    tm = ex.threat_model()
    assert len(tm["assets"]) >= 3 and len(tm["adversaries"]) >= 3
    assert len(tm["controls"]) >= 5
    for c in tm["controls"]:
        assert {"threat", "control", "principle"} <= set(c)
        assert c["principle"] in ex.PRINCIPLES, c["principle"]
    assert len({c["principle"] for c in tm["controls"]}) >= 4


def test_threat_model_covers_the_basics():
    tm = ex.threat_model()
    assert any("record" in a.lower() for a in tm["assets"])
    assert any("audit" in c["control"].lower() for c in tm["controls"])
    assert any(c["principle"] == "complete mediation" for c in tm["controls"])
