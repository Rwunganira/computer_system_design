import pytest
import requests

from course.testing import load_exercises

ex = load_exercises(__file__)  # also puts this lesson's folder on sys.path

from vax_client import VaxClient  # noqa: E402
from vax_server import DoseStore, create_app  # noqa: E402

DOSE = {"person_id": "P000001", "vaccine": "MCV1", "clinic_id": "C01", "dose_date": "2026-03-02"}


class FakePost:
    """A transport that fails a set number of times, then succeeds."""

    def __init__(self, failures, error=requests.Timeout):
        self.failures, self.error, self.calls = failures, error, []

    def __call__(self, url, json=None, headers=None, timeout=None):
        self.calls.append(timeout)
        if len(self.calls) <= self.failures:
            raise self.error("simulated")
        return "ok"


class FakeReply:
    """Just enough of a ``requests.Response`` for VaxClient."""

    def __init__(self, body, status_code):
        self.body, self.status_code = body, status_code

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.status_code)


# Exercise 1: timeouts and exponential backoff

def test_backoff_retries_until_success():
    post, waits = FakePost(failures=2), []
    assert ex.post_with_backoff(post, "http://vax/doses", DOSE, sleep=waits.append) == "ok"
    assert waits == [0.5, 1.0]
    assert post.calls == [2.0, 2.0, 2.0]  # every attempt uses the 2-second timeout


def test_backoff_gives_up_and_reraises():
    post, waits = FakePost(failures=99, error=requests.ConnectionError), []
    with pytest.raises(requests.ConnectionError):
        ex.post_with_backoff(post, "http://vax/doses", DOSE, retries=4, sleep=waits.append)
    assert len(post.calls) == 5
    assert waits == [0.5, 1.0, 2.0, 4.0]


def test_backoff_does_not_retry_other_errors():
    post, waits = FakePost(failures=1, error=ValueError), []
    with pytest.raises(ValueError):
        ex.post_with_backoff(post, "http://vax/doses", DOSE, sleep=waits.append)
    assert len(post.calls) == 1 and waits == []


# Exercise 2: the idempotency-key check on the server

@pytest.fixture
def app():
    return create_app(store=DoseStore(), handler=ex.record_dose_checked)


def test_same_key_twice_records_one_dose(app):
    client = app.test_client()
    first = client.post("/doses", json=DOSE, headers={"Idempotency-Key": "k1"})
    again = client.post("/doses", json=DOSE, headers={"Idempotency-Key": "k1"})
    assert first.status_code == 201 and again.status_code == 200
    assert again.get_json() == first.get_json()
    assert len(app.config["store"].doses) == 1


def test_different_keys_and_no_key_each_record(app):
    client = app.test_client()
    client.post("/doses", json=DOSE, headers={"Idempotency-Key": "k1"})
    client.post("/doses", json=DOSE, headers={"Idempotency-Key": "k2"})
    client.post("/doses", json=DOSE)
    client.post("/doses", json=DOSE)
    assert len(app.config["store"].doses) == 4


def test_reused_key_for_a_different_dose_is_rejected(app):
    client = app.test_client()
    client.post("/doses", json=DOSE, headers={"Idempotency-Key": "k1"})
    other = client.post("/doses", json={**DOSE, "vaccine": "BCG"}, headers={"Idempotency-Key": "k1"})
    assert other.status_code == 409
    assert [d["vaccine"] for d in app.config["store"].doses] == ["MCV1"]


def test_retrying_client_records_no_duplicate_doses(app):
    """The duplicate-dose test: replies are lost after the dose is saved."""
    flask_client = app.test_client()
    lost = {"count": 0}

    def lossy_post(url, json=None, headers=None, timeout=None):
        reply = flask_client.post("/doses", json=json, headers=headers)
        if lost["count"] < 2:  # the first two replies never reach the client
            lost["count"] += 1
            raise requests.Timeout("reply lost")
        return FakeReply(reply.get_json(), reply.status_code)

    client = VaxClient("http://vax", idempotent=True, post=lossy_post)
    client.record_dose(DOSE)
    assert client.timeouts_seen == 2
    assert len(app.config["store"].doses) == 1


# Exercise 3: the dashboard survives VaxRecords being down

def test_dashboard_counts_doses():
    client = create_app().test_client()
    client.post("/doses", json=DOSE)
    client.post("/doses", json={**DOSE, "person_id": "P000002"})
    assert ex.dose_total_for_dashboard(lambda path: client.get(path).get_json()) == 2


def test_dashboard_survives_unreachable_service():
    def down(path):
        raise requests.ConnectionError("VaxRecords is down")

    assert ex.dose_total_for_dashboard(down) is None
