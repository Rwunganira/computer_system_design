# Module 9. Atomicity

**Goal:** make recording a dose in VaxRecords an action that either happens completely or not at
all, even if the power fails halfway, and that never interleaves badly with another worker's dose.

**Read in the book:** Chapter 9, "Atomicity: All-or-Nothing and Before-or-After".

## The problem: one action, two writes

Recording a dose changes two things: the child's vaccination history and the clinic's vaccine
stock. The rule that ties them together, the **invariant**, is

    for every clinic and vaccine:  stock left + doses given = stock received

`dose_recorder_naive.py` writes the history file, then the stock file. Crash between the two and
the history says the dose was given while the stock says it was not. Restarting does not help:
nothing on disk records that an action was half done. In surveillance terms, coverage and stock
reports now disagree, and someone will spend a week reconciling them by hand.

## Two kinds of atomicity

The book names two properties, and they are different problems:

- **All-or-nothing atomicity:** a multi-step action either completes, or has no visible effect,
  despite crashes. This is about failures.
- **Before-or-after atomicity:** concurrent actions behave as if one ran completely before the
  other. This is about concurrency. Two health workers dispensing from the same stock at the same
  moment can both read "20 left", both write "19", and one dose disappears from the books: a **lost
  update** (Exercise 2).

A transaction in a database gives you both at once, which is why it is such a useful abstraction.

## All-or-nothing, three ways

Each fix needs a **commit point**: a single step that cannot be half done. Before it, a crash
means the action never happened; after it, a crash means it did and must be finished.

1. **Shadow copy** (`shadow_copy.py`). Put history and stock in one file. Write the whole new
   version to a temporary file, flush it to disk, then `os.replace` it over the old one. The
   rename is atomic, so it is the commit point. A crash leaves at worst a stray temporary file,
   which start-up deletes. Simple and robust, but every dose rewrites the whole file.
2. **Write-ahead log plus recovery** (`wal_recorder.py`). Append the intended changes to a log,
   then a COMMIT record (the commit point), and only then **install** the changes in the real
   files, finishing with an END record. The **write-ahead rule**: log before you install. After a
   crash, a **recovery procedure** runs on start-up: transactions with COMMIT but no END are
   **redone**; transactions without COMMIT are ignored, because nothing of theirs was installed.
   The example crashes before every step in turn: the files on disk are sometimes inconsistent
   right after the crash, but always consistent after recovery. Redo must be **idempotent**
   (setting stock to 19, not subtracting 1), because recovery itself can crash and run again.
3. **A database transaction** (`sqlite_txn.py`). SQLite does all of the above for you with its own
   journal. The example kills a real child process (`os._exit`) between two SQL statements: in
   autocommit mode the database is left inconsistent; inside `BEGIN ... COMMIT` it is not. A
   `CHECK (doses_left >= 0)` constraint is a fail-fast check that rolls the whole dose back.

In real work, use option 3. Options 1 and 2 are how option 3 works inside.

## Before-or-after: locks

Make the read and the write of the stock one indivisible step with respect to other workers by
holding a **lock** across both. Exercise 2 makes a lost update happen deterministically with a
barrier, then prevents it with `threading.Lock`. In a Flask app with several worker processes, a
Python lock is not enough: the lock has to live where the data lives (a database row lock, which
is what `BEGIN IMMEDIATE` takes in SQLite).

## Across services: two-phase commit

When history and stock belong to two separate services, no single file rename or local
transaction covers both. **Two-phase commit** (`two_phase_commit.py`) uses a coordinator:

- **Phase 1 (prepare):** each participant checks it can do its part, records the tentative change
  durably, and votes yes or no. Voting yes is a promise: "I can commit this even if I crash".
- **Commit point:** the coordinator writes its decision (commit only if *all* voted yes) to its log.
- **Phase 2:** the coordinator tells every participant the outcome; each commits or aborts.

The example shows the cost. When the coordinator crashes after deciding, both participants are
**prepared** and in doubt: they gave up the right to abort on their own and cannot learn the
outcome. They are **blocked**, holding the reserved stock, until the coordinator recovers and
resends its decision. Exercise 3 asks what each side should do when a message never arrives.

## Run the examples

From the repository root:

```bash
.venv/bin/python lessons/09_atomicity/dose_recorder_naive.py   # crash between two writes
.venv/bin/python lessons/09_atomicity/shadow_copy.py           # fix 1: temp file + os.replace
.venv/bin/python lessons/09_atomicity/wal_recorder.py          # fix 2: write-ahead log + recovery
.venv/bin/python lessons/09_atomicity/sqlite_txn.py            # fix 3: an SQLite transaction
.venv/bin/python lessons/09_atomicity/two_phase_commit.py      # across two services
.venv/bin/pytest lessons/09_atomicity                           # fails until you do the exercises
```

All examples work in temporary directories and leave no files behind.
