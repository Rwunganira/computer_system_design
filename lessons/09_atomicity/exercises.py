"""Module 9 exercises. Complete each TODO, then run: pytest lessons/09_atomicity"""

import threading

import wal_recorder


# Exercise 1. Recovery for the write-ahead log.
#
# The test crashes wal_recorder.record_dose before each of its steps in turn,
# then calls your recover() as if the program had just restarted, and checks
# that the files are consistent and that the dose is all there or not there.

def recover(folder):
    """Recovery procedure for the log written by ``wal_recorder.record_dose``.

    Read ``folder/wal.log`` (one JSON record per line; use wal_recorder.read_log
    as a starting point). For every transaction with a "commit" record but no
    "end" record, redo its "change" records in log order using
    ``wal_recorder.install``, then append an "end" record for it. Ignore
    transactions that never committed.

    Unlike wal_recorder.recover, yours must survive a *torn* final record: a
    crash in the middle of appending leaves a last line that is not valid JSON
    (and has no newline). Treat it as never written: drop it, and rewrite the
    log without it so later appends start on a clean line.

    Return the sorted list of tids you redid. Running recover twice in a row
    must be safe (the second run redoes nothing).
    """
    # TODO
    raise NotImplementedError


# Exercise 2. Lost updates and locks (before-or-after atomicity).
#
# Two health workers at the same clinic dispense a dose at the same moment.
# Each does read-modify-write on the shared stock. ``between`` is a hook the
# tests use to pause a worker between its read and its write.

def dispense_unlocked(stock, clinic_id, vaccine, between=None):
    """Given: read the stock, (maybe pause), write it back minus one."""
    left = stock[clinic_id][vaccine]
    if between:
        between()
    stock[clinic_id][vaccine] = left - 1


def show_lost_update(start=20):
    """Make a lost update happen, every time, and return the final stock.

    Start from ``{"C01": {"MCV1": start}}``. Run two threads that each call
    ``dispense_unlocked`` once, with a ``between`` hook that makes both threads
    finish their read before either writes (hint: threading.Barrier(2).wait).
    Two doses were given, but the stock should show only one: return it.
    """
    # TODO
    raise NotImplementedError


def dispense(stock, clinic_id, vaccine, lock, between=None):
    """Like dispense_unlocked, but before-or-after atomic: hold ``lock`` (a
    threading.Lock shared by all workers) across the read AND the write, so no
    other worker can read in between. Call ``between`` at the same place."""
    # TODO
    raise NotImplementedError


# Exercise 3. A participant that never answers.
#
# In two_phase_commit.py every participant answers promptly. Decide what each
# side should do when a message never comes.

def decide(votes):
    """The coordinator's decision after the prepare deadline has passed.

    ``votes`` maps participant name to "yes", "no", or None (no answer before the
    deadline). Return "commit" or "abort".
    """
    # TODO
    raise NotImplementedError


def participant_on_silence(status):
    """What a participant does when it has heard nothing from the coordinator
    for a long time. ``status`` is the participant's state for the transaction:
    None (asked to do work but not yet asked to prepare, or not yet voted),
    "prepared", "committed" or "aborted".

    Return "abort" if it may safely abort on its own, "wait" if it must keep
    waiting (and asking the coordinator) for the decision, or "nothing" if the
    transaction is already finished for it.
    """
    # TODO: think about what voting "yes" promised.
    raise NotImplementedError
