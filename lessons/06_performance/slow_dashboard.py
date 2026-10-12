"""A slow SurveilLite dashboard refresh, profiled with cProfile.

Refreshing the dashboard does three things, all of them naively:

1. fetch each clinic's weekly reports, one clinic after another (each fetch
   waits on a slow network, simulated here with time.sleep);
2. save every report row to SQLite, committing after each row;
3. for every clinic row on the page, compute its district's incidence from
   scratch, even though 40 clinics share only 8 districts.

Run it and read the profile. Do not guess where the time goes: measure.

    python lessons/06_performance/slow_dashboard.py
"""

import cProfile
import io
import pstats
import sqlite3
import tempfile
import time
from pathlib import Path

from course.data import DISTRICTS, DISEASES, case_reports, clinics

REPORTS = case_reports()            # 40 clinics x 12 weeks x 3 diseases = 1,440 rows
CLINICS = clinics()
POPULATION = DISTRICTS.set_index("district_id").population.to_dict()
FETCH_LATENCY = 0.02                # seconds per clinic: a slow rural connection
fetch_calls = 0                     # counted so the fixes can show they do the same work


def fetch_clinic_report(clinic_id):
    """Pretend to call a clinic's reporting server: wait, then return its rows."""
    global fetch_calls
    fetch_calls += 1
    time.sleep(FETCH_LATENCY)       # the network round trip; the CPU is idle meanwhile
    rows = REPORTS[REPORTS.clinic_id == clinic_id]
    return list(rows[["report_id", "clinic_id", "district_id", "disease", "cases"]]
                .itertuples(index=False, name=None))


def open_db(folder):
    conn = sqlite3.connect(Path(folder) / "surveillite.db")
    conn.execute("CREATE TABLE IF NOT EXISTS reports "
                 "(report_id INTEGER PRIMARY KEY, clinic_id, district_id, disease, cases)")
    return conn


def save_reports_slow(conn, rows):
    """One INSERT and one COMMIT per row: every commit waits for the disk."""
    for row in rows:
        conn.execute("INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?)", row)
        conn.commit()


def district_incidence(district_id, disease):
    """Cases per 100,000 in a district, recomputed from all reports every call."""
    mask = (REPORTS.district_id == district_id) & (REPORTS.disease == disease)
    return REPORTS[mask].cases.sum() / POPULATION[district_id] * 100_000


def build_page(incidence):
    """One line per clinic and disease, each showing its district's incidence."""
    lines = []
    for c in CLINICS.itertuples():
        for disease in DISEASES:
            lines.append(f"{c.clinic_id} {disease:<8} {incidence(c.district_id, disease):8.1f}")
    return lines


def refresh_dashboard(folder):
    rows = []
    for clinic_id in CLINICS.clinic_id:          # one clinic at a time
        rows.extend(fetch_clinic_report(clinic_id))
    conn = open_db(folder)
    save_reports_slow(conn, rows)
    conn.close()
    return build_page(district_incidence)


def main():
    with tempfile.TemporaryDirectory() as folder:
        profiler = cProfile.Profile()
        start = time.perf_counter()
        profiler.enable()
        page = refresh_dashboard(folder)
        profiler.disable()
        elapsed = time.perf_counter() - start

    print(f"Dashboard refresh: {len(page)} lines in {elapsed:.2f} s "
          f"({fetch_calls} fetches)\n")

    def table(sort, *restrictions):
        out = io.StringIO()
        pstats.Stats(profiler, stream=out).strip_dirs().sort_stats(sort).print_stats(*restrictions)
        text = out.getvalue()
        return text[text.index("   ncalls"):].rstrip()   # skip pstats' preamble

    print("Top 6 by tottime (where the time is actually spent):")
    print(table("tottime", 6))
    print("\nOur own functions by cumtime (who asked for that time):")
    print(table("cumtime", "slow_dashboard"))
    print("\ntottime = time spent inside the function itself; cumtime = including what it calls.")
    print("Which rows are waiting (disk, network) and which are computing?")
    print("Run dashboard_fixes.py to measure one fix at a time.")


if __name__ == "__main__":
    main()
