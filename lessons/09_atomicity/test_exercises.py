import threading
import time

import pytest

from course.testing import load_exercises

ex = load_exercises(__file__)  # also puts this lesson folder on sys.path

import two_phase_commit  # noqa: E402  (the lesson's example modules)
import wal_recorder  # noqa: E402
from dose_recorder_naive import Crash, crash_at, is_consistent, load, sample_doses, setup  # noqa: E402

DOSES = sample_doses(3)


def dose_recorded(folder, dose):
    history, _ = load(folder)
    return any(d["dose_id"] == dose["dose_id"] for d in history.get(dose["person_id"], []))


# Exercise 1: crash at every step, then recover

@pytest.mark.parametrize("step", range(len(wal_recorder.STEPS) + 1))
def test_recovery_after_crash_at_every_step(tmp_path, step):
    setup(tmp_path)
    wal_recorder.record_dose(tmp_path, DOSES[0])
    try:
        wal_recorder.record_dose(tmp_path, DOSES[1], hook=crash_at(step))
    except Crash:
        pass
    ex.recover(tmp_path)
    assert is_consistent(*load(tmp_path))
    # All or nothing: the dose survives exactly when the crash came after COMMIT was logged.
    assert dose_recorded(tmp_path, DOSES[1]) == (step > wal_recorder.COMMIT_STEP)
    assert dose_recorded(tmp_path, DOSES[0])
    # Recovery is idempotent, and the system keeps working afterwards.
    assert ex.recover(tmp_path) == []
    wal_recorder.record_dose(tmp_path, DOSES[2])
    assert is_consistent(*load(tmp_path)) and dose_recorded(tmp_path, DOSES[2])


def test_recover_reports_redone_tids(tmp_path):
    setup(tmp_path)
    with pytest.raises(Crash):
        wal_recorder.record_dose(tmp_path, DOSES[0], hook=crash_at(4))
    assert ex.recover(tmp_path) == [DOSES[0]["dose_id"]]


def test_recovery_survives_torn_final_record(tmp_path):
    setup(tmp_path)
    wal_recorder.record_dose(tmp_path, DOSES[0])
    with pytest.raises(Crash):
        wal_recorder.record_dose(tmp_path, DOSES[1], hook=crash_at(wal_recorder.COMMIT_STEP))
    with open(tmp_path / "wal.log", "a") as f:
        f.write('{"tid": %d, "type": "comm' % DOSES[1]["dose_id"])   # crash mid-append
    assert ex.recover(tmp_path) == []
    assert is_consistent(*load(tmp_path)) and not dose_recorded(tmp_path, DOSES[1])
    wal_recorder.record_dose(tmp_path, DOSES[2])
    assert all(isinstance(r, dict) for r in wal_recorder.read_log(tmp_path))  # the log parses again


# Exercise 2: lost update, then locking

def test_lost_update_happens():
    assert ex.show_lost_update(start=20) == 19


def test_lock_prevents_lost_update():
    stock = {"C01": {"MCV1": 20}}
    lock = threading.Lock()
    workers = [threading.Thread(target=ex.dispense, args=(stock, "C01", "MCV1", lock, lambda: time.sleep(0.01)))
               for _ in range(2)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    assert stock["C01"]["MCV1"] == 18


def test_many_workers_with_lock():
    stock = {"C01": {"MCV1": 1_000}}
    lock = threading.Lock()

    def worker():
        for _ in range(50):
            ex.dispense(stock, "C01", "MCV1", lock, between=lambda: time.sleep(0))

    workers = [threading.Thread(target=worker) for _ in range(8)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    assert stock["C01"]["MCV1"] == 1_000 - 8 * 50


# Exercise 3: a participant that never answers

@pytest.mark.parametrize("votes, expected", [
    ({"VaxRecords": "yes", "Stock": "yes"}, "commit"),
    ({"VaxRecords": "yes", "Stock": "no"}, "abort"),
    ({"VaxRecords": "yes", "Stock": None}, "abort"),
    ({"VaxRecords": None, "Stock": None}, "abort"),
])
def test_coordinator_decision(votes, expected):
    assert ex.decide(votes) == expected


def test_participant_on_silence():
    assert ex.participant_on_silence(None) == "abort"
    assert ex.participant_on_silence("prepared") == "wait"
    assert ex.participant_on_silence("committed") == "nothing"
    assert ex.participant_on_silence("aborted") == "nothing"


def test_prepared_participants_in_the_example_must_wait():
    vax, stock = two_phase_commit.VaxRecordsService(), two_phase_commit.StockService()
    coord = two_phase_commit.Coordinator([vax, stock])
    with pytest.raises(Crash):
        coord.run("t1", DOSES[0], crash_after_decision=True)
    assert [ex.participant_on_silence(p.status.get("t1")) for p in (vax, stock)] == ["wait", "wait"]
