import pytest

from course.data import case_reports
from course.testing import load_exercises

ex = load_exercises(__file__)
import sms_reports  # noqa: E402  (importable once load_exercises has put the lesson on sys.path)


@pytest.fixture(scope="module")
def messages():
    reports = case_reports(weeks=4)
    return sms_reports.as_messages(reports[reports.disease == "cholera"])


# Exercise 1 ----------------------------------------------------------------

def test_checksum_round_trip():
    text = "DATA|C01|1|2026-01-05|3"
    assert ex.verify(ex.add_checksum(text)) == text


def test_every_single_character_change_is_detected():
    wire = ex.add_checksum("DATA|C07|12|2026-02-02|41")
    for i, ch in enumerate(wire):
        for replacement in "0123456789#|X":
            if replacement != ch:
                garbled = wire[:i] + replacement + wire[i + 1:]
                assert ex.verify(garbled) is None, f"missed change at {i}: {garbled!r}"


def test_verify_rejects_garbage():
    for junk in ["", "hello", "DATA|C01|1|2026-01-05|3", "abc#", "#"]:
        assert ex.verify(junk) is None


def test_totals_correct_over_a_corrupting_channel(messages):
    up = sms_reports.SmsChannel(corrupt=0.1, seed=2)
    down = sms_reports.SmsChannel(corrupt=0.1, seed=3)
    result = sms_reports.send_reliably(messages, up, down, encode=ex.add_checksum, decode=ex.verify)
    assert result.corrupted_dropped > 0
    assert sms_reports.district_totals(result.records) == sms_reports.district_totals(messages)


# Exercise 2 ----------------------------------------------------------------

def test_texts_sent_grows_with_loss(messages):
    sent = ex.texts_sent(messages, [0.1, 0.3, 0.5])
    assert list(sent) == [0.1, 0.3, 0.5]
    assert len(messages) < sent[0.1] < sent[0.3] < sent[0.5]
    assert sent[0.5] > 3 * len(messages)        # roughly 1 / (1 - p)**2 = 4 per report


def test_texts_sent_without_loss(messages):
    assert ex.texts_sent(messages, [0.0]) == {0.0: len(messages)}


# Exercise 3 ----------------------------------------------------------------

def test_where_to_check():
    assert ex.where_to_check() == "district office"


def test_clinics_with_wrong_totals():
    records = [("C01", "w1", 3), ("C01", "w2", 4), ("C02", "w1", 5), ("C02", "w1", 5)]
    claimed = {"C01": 7, "C02": 5, "C03": 0}
    assert ex.clinics_with_wrong_totals(records, claimed) == ["C02", "C03"]


def test_end_to_end_check_catches_a_naive_channel(messages):
    records = sms_reports.send_naively(messages, sms_reports.SmsChannel(seed=1))
    claimed = {}
    for clinic_id, _week, cases in messages:
        claimed[clinic_id] = claimed.get(clinic_id, 0) + cases
    assert ex.clinics_with_wrong_totals(messages, claimed) == []
    assert ex.clinics_with_wrong_totals(records, claimed) != []
