# Predict, then run

Answer each question in a sentence before running the examples in `lessons/09_atomicity/`.

1. `dose_recorder_naive.py` crashes after writing the history but before writing the stock. After a
   restart, will the dashboard over- or under-report the doses left at that clinic? Could a
   recovery procedure fix it, given only the two files?
2. `wal_recorder.py` crashes before each of its six steps in turn. For which crash points will the
   second dose be in the history after recovery? At which crash point will the files on disk be
   inconsistent *before* recovery runs?
3. `sqlite_txn.py` kills the process between the INSERT and the UPDATE. With a transaction, will
   the reopened database contain the half-recorded dose? Who removes it, and when?
4. In `two_phase_commit.py` the coordinator crashes after logging "commit" but before telling the
   participants. Can VaxRecords show the dose to a nurse during that time? Can the stock service
   give the reserved dose to another child?
