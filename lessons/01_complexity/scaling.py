"""Incommensurate scaling: a duplicate check that is fine for one clinic and hopeless nationally.

A report is a duplicate if another report has the same clinic, week and disease
(a clinic pressed "send" twice). Two ways to find them:

- naive: compare every report with every other report. Work grows with n squared.
- set-based: remember each (clinic, week, disease) key as you go. Work grows with n.

    python lessons/01_complexity/scaling.py
"""

import random
import time


def make_reports(n, seed=1):
    """n synthetic report keys with about 1% duplicates."""
    rng = random.Random(seed)
    # Every original report has a unique (clinic, week, disease) key.
    reports = [(f"C{i % 40 + 1:02d}", i // 120, ("measles", "cholera", "malaria")[i // 40 % 3], rng.randrange(20))
               for i in range(n)]
    for _ in range(n // 100):  # resend some reports
        reports.append(rng.choice(reports))
    return reports


def duplicates_naive(reports):
    found = 0
    for i in range(len(reports)):
        for j in range(i + 1, len(reports)):
            if reports[i][:3] == reports[j][:3]:
                found += 1
                break
    return found


def duplicates_with_set(reports):
    seen, found = set(), 0
    for r in reports:
        key = r[:3]
        if key in seen:
            found += 1
        seen.add(key)
    return found


def timed(fn, data):
    start = time.perf_counter()
    result = fn(data)
    return result, time.perf_counter() - start


if __name__ == "__main__":
    print(f"{'reports':>9} {'naive (s)':>10} {'set (s)':>9} {'duplicates':>11}")
    for n in (500, 1_000, 2_000, 4_000):
        data = make_reports(n)
        dup_a, t_naive = timed(duplicates_naive, data)
        dup_b, t_set = timed(duplicates_with_set, data)
        assert dup_a == dup_b
        print(f"{len(data):>9,} {t_naive:>10.3f} {t_set:>9.4f} {dup_b:>11}")
    data = make_reports(1_000_000)
    dups, t_set = timed(duplicates_with_set, data)
    print(f"{len(data):>9,} {'(skipped)':>10} {t_set:>9.4f} {dups:>11}")
    print("\nEach doubling makes the naive check about 4x slower; the set check only 2x. Predict the skipped cell.")
