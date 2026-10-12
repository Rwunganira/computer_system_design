"""Fix 1: a shadow copy. Write the whole new state elsewhere, then switch to it in one step.

History and stock now live in one file, state.json. To record a dose we write
a complete new version to state.json.tmp (the shadow) and then call os.replace,
which renames it over state.json. On POSIX and Windows that rename is atomic:
afterwards the name points at either the old file or the new one, never a mix.
The rename is the commit point.
"""

import json
import os
import tempfile
from pathlib import Path

from dose_recorder_naive import Crash, add_dose, crash_at, initial_stock, is_consistent, sample_doses

STEPS = ["write first half of shadow", "write second half of shadow", "fsync shadow", "os.replace (commit)"]


def setup(folder):
    (Path(folder) / "state.json").write_text(json.dumps({"history": {}, "stock": initial_stock()}))


def recover(folder):
    """On start-up: a leftover shadow is an uncommitted update. Throw it away."""
    shadow = Path(folder) / "state.json.tmp"
    if shadow.exists():
        shadow.unlink()
        return True
    return False


def load(folder):
    state = json.loads((Path(folder) / "state.json").read_text())
    return state["history"], state["stock"]


def record_dose(folder, dose, hook=None):
    hook = hook or (lambda i: None)
    history, stock = load(folder)
    add_dose(history, dose)
    stock[dose["clinic_id"]][dose["vaccine"]] -= 1
    new = json.dumps({"history": history, "stock": stock}).encode()

    shadow, target = Path(folder) / "state.json.tmp", Path(folder) / "state.json"
    with open(shadow, "wb") as f:
        hook(0)
        f.write(new[: len(new) // 2])
        f.flush()
        hook(1)                       # a crash here leaves a torn shadow file
        f.write(new[len(new) // 2:])
        hook(2)
        f.flush()
        os.fsync(f.fileno())          # make sure the shadow is on disk before we commit
    hook(3)
    os.replace(shadow, target)        # the commit point: one atomic rename


def describe(folder, dose):
    history, stock = load(folder)
    given = sum(len(v) for v in history.values())
    left = stock[dose["clinic_id"]][dose["vaccine"]]
    ok = "consistent" if is_consistent(history, stock) else "INCONSISTENT"
    return f"{given} doses, {dose['clinic_id']} {dose['vaccine']} stock = {left} -> {ok}"


def main():
    doses = sample_doses(2)
    print("Crash at each step of recording the second dose, then restart:\n")
    for step, name in enumerate(STEPS + [None]):
        with tempfile.TemporaryDirectory() as folder:
            setup(folder)
            record_dose(folder, doses[0])
            try:
                record_dose(folder, doses[1], hook=crash_at(step))
            except Crash:
                pass
            discarded = recover(folder)
            note = "shadow discarded" if discarded else ""
            label = f"crash before {name}" if name else "no crash"
            print(f"  {label:<41} {describe(folder, doses[1])}  {note}")
    print("\nEvery outcome is consistent: the dose is either fully recorded or not at all.")
    print("Cost: every dose rewrites the whole file. Fine for one clinic, not for a country.")


if __name__ == "__main__":
    main()
