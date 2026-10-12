# Predict, then run

Answer each question in a sentence before running `python lessons/05_virtualization/lab_pipeline.py`.

1. The unlocked counter runs three times on the same files. Will it give the same wrong total each
   time, a different wrong total, or sometimes the right one? Will it ever count *more* positives
   than there are?
2. Will the number of valid rows be wrong too in the unlocked runs? (Look at how consumers store
   rows.)
3. The buffer holds only 8 results while the files hold 2,000. Will a small buffer change the
   totals, or only the timing? What would happen if a producer dropped a result whenever the
   buffer was full?
4. Remove the `time.sleep(0)` from `Counter._read_modify_write` and run again. Do you still see lost
   updates? Does that mean the unlocked counter is now correct?
