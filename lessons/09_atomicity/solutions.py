"""Module 9 worked answers."""

import json
import threading
from pathlib import Path

import wal_recorder


def recover(folder):
    path = Path(folder) / "wal.log"
    if not path.exists():
        return []
    log, lines = [], path.read_text().splitlines()
    for i, line in enumerate(lines):
        try:
            log.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(lines) - 1:
                raise                      # damage in the middle is not a torn tail: fail fast
            # torn tail: rewrite the log without it
            path.write_text("".join(json.dumps(r) + "\n" for r in log))
    committed = {r["tid"] for r in log if r["type"] == "commit"}
    ended = {r["tid"] for r in log if r["type"] == "end"}
    todo = committed - ended
    for r in log:
        if r["type"] == "change" and r["tid"] in todo:
            wal_recorder.install(folder, r)
    for tid in sorted(todo):
        wal_recorder.append_log(folder, {"tid": tid, "type": "end"})
    return sorted(todo)


def dispense_unlocked(stock, clinic_id, vaccine, between=None):
    left = stock[clinic_id][vaccine]
    if between:
        between()
    stock[clinic_id][vaccine] = left - 1


def show_lost_update(start=20):
    stock = {"C01": {"MCV1": start}}
    barrier = threading.Barrier(2)
    workers = [threading.Thread(target=dispense_unlocked, args=(stock, "C01", "MCV1", barrier.wait))
               for _ in range(2)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    return stock["C01"]["MCV1"]


def dispense(stock, clinic_id, vaccine, lock, between=None):
    with lock:
        left = stock[clinic_id][vaccine]
        if between:
            between()
        stock[clinic_id][vaccine] = left - 1


def decide(votes):
    # Silence is not consent: only a unanimous, explicit yes may commit.
    return "commit" if votes and all(v == "yes" for v in votes.values()) else "abort"


def participant_on_silence(status):
    if status is None:
        return "abort"      # it has promised nothing; the coordinator will see no "yes"
    if status == "prepared":
        return "wait"       # it promised to commit if told to: it is blocked until it learns the outcome
    return "nothing"
