"""Three fixes for slow_dashboard.py, measured one at a time.

Each fix is one of the book's general techniques:

1. concurrency: fetch clinic reports in parallel threads, overlapping the waits;
2. batching:    save all rows with executemany() in ONE transaction;
3. caching:     remember each district's incidence with functools.lru_cache.

Every fix must give the same answer as the slow version: a faster wrong
dashboard is worse than a slow right one.

    python lessons/06_performance/dashboard_fixes.py
"""

import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

import slow_dashboard as slow


def save_reports_batched(conn, rows):
    """All rows in one transaction: the disk is forced once, not once per row."""
    with conn:                                   # BEGIN ... COMMIT (or ROLLBACK on error)
        conn.executemany("INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?, ?)", rows)


@lru_cache(maxsize=64)                           # the working set is 8 districts x 3 diseases
def cached_incidence(district_id, disease):
    return slow.district_incidence(district_id, disease)


def fetch_all_concurrently(clinic_ids, workers=10):
    """Up to ``workers`` fetches wait on the network at the same time."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(slow.fetch_clinic_report, clinic_ids)   # keeps input order
        return [row for rows in results for row in rows]


def timed(label, fn, *args):
    start = time.perf_counter()
    result = fn(*args)
    print(f"  {label:<34} {time.perf_counter() - start:6.3f} s")
    return result


def count_rows(conn):
    return conn.execute("SELECT COUNT(*), SUM(cases) FROM reports").fetchone()


def main():
    clinic_ids = list(slow.CLINICS.clinic_id)

    print("Fix 1: concurrency, fetching 40 clinic reports")
    calls_before = slow.fetch_calls
    rows_seq = timed("one clinic after another", lambda: [r for c in clinic_ids
                                                          for r in slow.fetch_clinic_report(c)])
    rows_par = timed("10 threads at once", fetch_all_concurrently, clinic_ids)
    print(f"  same rows: {rows_seq == rows_par}; fetch calls made: {slow.fetch_calls - calls_before}"
          f" (40 each way)\n  Latency of each fetch is unchanged; we overlapped the waiting.\n")

    print(f"Fix 2: batching {len(rows_seq):,} inserts into SQLite")
    with tempfile.TemporaryDirectory() as folder:
        conn = slow.open_db(folder)
        timed("commit after every row", slow.save_reports_slow, conn, rows_seq)
        slow_result = count_rows(conn)
        conn.execute("DELETE FROM reports")
        conn.commit()
        timed("executemany, one transaction", save_reports_batched, conn, rows_seq)
        print(f"  same table: {slow_result == count_rows(conn)} (rows, total cases = {slow_result})")
        conn.close()
    print("  The cost was per-commit overhead (waiting for the disk), not the inserts.\n")

    print("Fix 3: caching district incidence while building the page (120 lookups)")
    page_slow = timed("recompute every time", slow.build_page, slow.district_incidence)
    page_fast = timed("lru_cache", slow.build_page, cached_incidence)
    info = cached_incidence.cache_info()
    print(f"  same page: {page_slow == page_fast}; hits={info.hits} misses={info.misses} "
          f"hit rate={info.hits / (info.hits + info.misses):.0%}")
    print("  Small win: this was never the bottleneck. And new reports will NOT appear")
    print("  until the cache is invalidated (exercise 2).\n")

    print("All three together:")
    cached_incidence.cache_clear()
    with tempfile.TemporaryDirectory() as folder:
        def refresh_fast():
            rows = fetch_all_concurrently(clinic_ids)
            conn = slow.open_db(folder)
            save_reports_batched(conn, rows)
            conn.close()
            return slow.build_page(cached_incidence)
        page = timed("fast refresh", refresh_fast)
    print(f"  same page as the slow refresh: {page == page_slow}")


if __name__ == "__main__":
    main()
