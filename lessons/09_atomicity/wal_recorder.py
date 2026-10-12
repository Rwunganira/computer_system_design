"""Fix 2: a write-ahead log (WAL) plus a recovery procedure that runs on start-up.

Before touching history.json or stock.json, append what we are about to do to
an append-only log, then a COMMIT record. Only then install the changes in the
two files. The rule is "log first, install second" (write-ahead). A crash
leaves the log as the truth:

- no COMMIT for a transaction: it never happened; nothing was installed.
- COMMIT but no END: it happened; recovery redoes the installs.

Redo must be safe to repeat (idempotent), because recovery itself can crash.
"""

import json
import tempfile
from pathlib import Path

from dose_recorder_naive import (Crash, add_dose, crash_at, is_consistent, load, read_json,
                                 sample_doses, setup, write_json)

STEPS = ["log history change", "log stock change", "log COMMIT",
         "install history", "install stock", "log END"]
COMMIT_STEP = STEPS.index("log COMMIT")


def append_log(folder, record):
    with open(Path(folder) / "wal.log", "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()                    # a real system would also os.fsync here


def read_log(folder):
    path = Path(folder) / "wal.log"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def install(folder, change):
    """Apply one logged change. Idempotent: applying it twice is the same as once."""
    if change["file"] == "history":
        history = read_json(Path(folder) / "history.json")
        add_dose(history, change["dose"])
        write_json(Path(folder) / "history.json", history)
    else:
        stock = read_json(Path(folder) / "stock.json")
        stock[change["clinic_id"]][change["vaccine"]] = change["value"]  # a new value, not "-1"
        write_json(Path(folder) / "stock.json", stock)


def record_dose(folder, dose, hook=None):
    hook = hook or (lambda i: None)
    _, stock = load(folder)
    tid = dose["dose_id"]
    left = stock[dose["clinic_id"]][dose["vaccine"]] - 1
    changes = [
        {"tid": tid, "type": "change", "file": "history", "dose": dose},
        {"tid": tid, "type": "change", "file": "stock", "clinic_id": dose["clinic_id"],
         "vaccine": dose["vaccine"], "value": left},
    ]
    hook(0); append_log(folder, changes[0])
    hook(1); append_log(folder, changes[1])
    hook(2); append_log(folder, {"tid": tid, "type": "commit"})   # the commit point
    hook(3); install(folder, changes[0])
    hook(4); install(folder, changes[1])
    hook(5); append_log(folder, {"tid": tid, "type": "end"})       # installs are done


def recover(folder):
    """Run on start-up. Redo committed-but-unfinished transactions, in log order.
    Returns the tids it redid."""
    log = read_log(folder)
    committed = {r["tid"] for r in log if r["type"] == "commit"}
    ended = {r["tid"] for r in log if r["type"] == "end"}
    todo = committed - ended
    for r in log:
        if r["type"] == "change" and r["tid"] in todo:
            install(folder, r)
    for tid in sorted(todo):
        append_log(folder, {"tid": tid, "type": "end"})
    return sorted(todo)


def describe(folder, dose):
    history, stock = load(folder)
    given = sum(len(v) for v in history.values())
    left = stock[dose["clinic_id"]][dose["vaccine"]]
    ok = "consistent" if is_consistent(history, stock) else "INCONSISTENT"
    return f"{given} doses, stock {left:>2} -> {ok}"


def main():
    doses = sample_doses(2)
    print("Crash at each step of recording the second dose, look at the files, then recover:\n")
    print(f"  {'crash before':<20} {'on disk after the crash':<36} after recovery")
    for step, name in enumerate(STEPS + [None]):
        with tempfile.TemporaryDirectory() as folder:
            setup(folder)
            record_dose(folder, doses[0])
            try:
                record_dose(folder, doses[1], hook=crash_at(step))
            except Crash:
                pass
            before = describe(folder, doses[1])
            redone = recover(folder)
            after = describe(folder, doses[1]) + (f"  (redid tid {redone[0]})" if redone else "")
            print(f"  {name or '(no crash)':<20} {before:<36} {after}")
    print("\nThe files on disk can be inconsistent after a crash (step 'install stock'),")
    print("but recovery always reaches a consistent state: all of the dose, or none of it.")
    print("Crashing after COMMIT keeps the dose; crashing before it loses it cleanly.")


if __name__ == "__main__":
    main()
