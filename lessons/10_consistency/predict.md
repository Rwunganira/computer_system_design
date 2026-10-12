# Predict, then run

Answer each question in a sentence before running `python lessons/10_consistency/offline_sync.py`.

1. Tablet B records its dose 15 minutes *after* tablet A, but its clock runs 30 minutes slow. Under
   last-writer-wins, whose dose survives? Would the answer change if B's clock were correct?
2. With correct clocks, could last-writer-wins still lose a dose? What would have to happen?
3. After tablet A syncs, the server's version vector is `{"server": 1, "tablet-A": 1}` and tablet
   B's is `{"server": 1, "tablet-B": 1}`. Which of before, after, equal or concurrent is that?
4. If tablet B synced a second time right after the merge, would the server's record change?
