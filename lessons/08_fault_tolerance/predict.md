# Predict, then run

Answer each question in a sentence before running the examples in `lessons/08_fault_tolerance/`.

1. `checksummed_store.py` flips one bit in the last digit of a CSV of weekly cholera counts. Will
   pandas or `int()` raise an error when reading the damaged file? Will the total be off by a
   little or by a lot?
2. In `tmr_incidence.py` replica B misses the last six weeks of data. For which districts will its
   answer differ from A and C, and will the voter's output match A exactly?
3. If two of the three replicas share the same stale data, what will the voter report: an error,
   the right answer, or the wrong answer?
4. `availability.py` puts four parts in series, the worst of which is available about 98% of the
   time. Will the dashboard as a whole be above or below 98%? Which single part, duplicated, will
   help most?
