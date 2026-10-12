"""Recording a dose takes two writes. Crash between them and the data is inconsistent.

VaxRecords keeps two files: history.json (each child's doses) and stock.json
(doses left at each clinic). Recording a dose appends to the history AND
decrements the stock. The invariant that must always hold:

    for every clinic and vaccine:  stock left + doses given == INITIAL_STOCK

This file also holds the helpers the other examples in this module share.
"""

import json
import tempfile
from collections import Counter
from pathlib import Path

from course.data import VACCINES, clinics, population, vaccinations

INITIAL_STOCK = 20


class Crash(Exception):
    """Stands in for the power going out: the program stops right here."""


def crash_at(step):
    """A hook that crashes when the recorder reaches step number ``step``."""
    def hook(i):
        if i == step:
            raise Crash(f"crash before step {i}")
    return hook


def sample_doses(n=4):
    """A few real-looking doses from the synthetic data, as plain dicts."""
    doses = vaccinations(population(50)).head(n)
    return [{"dose_id": int(d.dose_id), "person_id": d.person_id, "vaccine": d.vaccine,
             "clinic_id": d.clinic_id} for d in doses.itertuples()]


def initial_stock():
    return {c: {v: INITIAL_STOCK for v in VACCINES} for c in clinics().clinic_id}


def is_consistent(history, stock):
    given = Counter((d["clinic_id"], d["vaccine"]) for doses in history.values() for d in doses)
    return all(stock[c][v] + given[(c, v)] == INITIAL_STOCK for c in stock for v in stock[c])


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=1))


def setup(folder):
    """Create an empty history and full stock in ``folder``."""
    write_json(Path(folder) / "history.json", {})
    write_json(Path(folder) / "stock.json", initial_stock())


def load(folder):
    return read_json(Path(folder) / "history.json"), read_json(Path(folder) / "stock.json")


def add_dose(history, dose):
    """Add ``dose`` to the child's history (idempotent: adding twice changes nothing)."""
    doses = history.setdefault(dose["person_id"], [])
    if dose["dose_id"] not in {d["dose_id"] for d in doses}:
        doses.append(dose)


def record_dose(folder, dose, hook=None):
    """The naive way: write the history, then write the stock."""
    hook = hook or (lambda i: None)
    history, stock = load(folder)
    add_dose(history, dose)
    stock[dose["clinic_id"]][dose["vaccine"]] -= 1

    hook(0)
    write_json(Path(folder) / "history.json", history)    # write 1
    hook(1)
    write_json(Path(folder) / "stock.json", stock)        # write 2


def describe(folder, dose):
    history, stock = load(folder)
    given = sum(len(v) for v in history.values())
    left = stock[dose["clinic_id"]][dose["vaccine"]]
    ok = "consistent" if is_consistent(history, stock) else "INCONSISTENT"
    return f"{given} doses in history, {dose['clinic_id']} {dose['vaccine']} stock = {left}  -> {ok}"


def main():
    first, second = sample_doses(2)
    with tempfile.TemporaryDirectory() as folder:
        setup(folder)
        record_dose(folder, first)
        print(f"After one dose:            {describe(folder, first)}")

        try:
            record_dose(folder, second, hook=crash_at(1))  # between write 1 and write 2
        except Crash as e:
            print(f"\nRecording a second dose... {e} (stock write)")
        print(f"After the crash:           {describe(folder, second)}")
        print("\nThe child's history says the dose was given, but the clinic's stock was never")
        print("decremented. Restarting the program does not help: nothing on disk says a")
        print("dose was half-recorded. The fixes: shadow_copy.py, wal_recorder.py, sqlite_txn.py.")


if __name__ == "__main__":
    main()
