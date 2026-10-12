"""A scripted bad week for the capstone system.

Everything that the course covered goes wrong at once:

  1. A clinic's phone retries a report it already sent (the reply was lost).
  2. An offline clinic comes back and sends three weeks of reports out of order.
  3. A disk silently corrupts one replica of a stored report.
  4. A clinic user tries to read another district's data; another submits for a clinic not their own.

The script runs the week against a set of parts and compares the dashboard
with the true numbers.

    python lessons/12_capstone/bad_week.py              # naive parts, then your exercises.py
    python lessons/12_capstone/bad_week.py --solutions  # naive parts, then the worked answers
"""

import json
import sys
import tempfile
from pathlib import Path

from surveillance_system import NaiveParts, create_app

USERS = {
    "tok-c31": {"name": "nurse_c31", "role": "clinic", "clinic_id": "C31"},       # a Coastal clinic
    "tok-c32": {"name": "nurse_c32", "role": "clinic", "clinic_id": "C32"},       # another Coastal clinic
    "tok-coa": {"name": "officer_coa", "role": "district_officer", "district_id": "S-COA"},
    "tok-hil": {"name": "officer_hil", "role": "district_officer", "district_id": "N-HIL"},
}
TRUE_CHOLERA_COASTAL = 40 + 25 + 31 + 44  # what actually happened, from the four reports below


def report(clinic_id, seq, week, cases):
    return {"clinic_id": clinic_id, "seq": seq, "week_start": week, "disease": "cholera", "cases": cases}


def run_week(parts):
    """Run the scenario; return a dict of observations."""
    with tempfile.TemporaryDirectory() as tmp:
        app = create_app(parts, tmp, USERS)
        c = app.test_client()
        auth = lambda tok: {"Authorization": f"Bearer {tok}"}

        # 1. Normal report, then the same report retried after a lost reply.
        c.post("/reports", json=report("C31", 1, "2026-03-02", 40), headers=auth("tok-c31"))
        c.post("/reports", json=report("C31", 1, "2026-03-02", 40), headers=auth("tok-c31"))

        # 2. C32 was offline; its reports arrive late and out of order.
        for seq, week, cases in [(3, "2026-03-16", 44), (1, "2026-03-02", 25), (2, "2026-03-09", 31)]:
            c.post("/reports", json=report("C32", seq, week, cases), headers=auth("tok-c32"))

        # 3. Silent corruption: a bit flips in replica 1 of one stored report.
        victim = next((Path(tmp) / "replica1").glob("C32_2_*.json"))
        rec = json.loads(victim.read_text())
        rec["payload"]["cases"] = 310  # 31 became 310; the checksum still says 31
        victim.write_text(json.dumps(rec, sort_keys=True))

        # 4. Misuse.
        snoop = c.get("/districts/S-COA/incidence", headers=auth("tok-hil")).status_code
        forged = c.post("/reports", json=report("C01", 1, "2026-03-02", 999), headers=auth("tok-c31")).status_code

        dash = c.get("/districts/S-COA/incidence", headers=auth("tok-coa")).get_json()
        return {
            "cholera_cases": dash["cases"].get("cholera", 0),
            "true_cases": TRUE_CHOLERA_COASTAL,
            "other_district_read": snoop,
            "forged_submit": forged,
            "audit_entries": len(app.config["AUDIT"]),
        }


def show(label, obs):
    ok = obs["cholera_cases"] == obs["true_cases"] and obs["other_district_read"] == 403 and obs["forged_submit"] == 403
    print(f"--- {label} ---")
    print(f"  Coastal cholera on dashboard: {obs['cholera_cases']}  (truth: {obs['true_cases']})")
    print(f"  Hillview officer reading Coastal: HTTP {obs['other_district_read']}  (should be 403)")
    print(f"  Clinic C31 submitting as C01:    HTTP {obs['forged_submit']}  (should be 403)")
    print(f"  Survived the bad week: {'YES' if ok else 'NO'}\n")


if __name__ == "__main__":
    show("naive parts", run_week(NaiveParts))
    sys.path.insert(0, str(Path(__file__).parent))
    if "--solutions" in sys.argv:
        import solutions as parts
        label = "worked answers"
    else:
        import exercises as parts
        label = "your exercises.py"
    try:
        show(label, run_week(parts))
    except NotImplementedError:
        print(f"--- {label} ---\n  Not finished yet: complete the TODOs in exercises.py.")
