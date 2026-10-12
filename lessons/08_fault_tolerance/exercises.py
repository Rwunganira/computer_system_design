"""Module 8 exercises. Complete each TODO, then run: pytest lessons/08_fault_tolerance"""

import checksummed_store
import tmr_incidence


# Exercise 1. Fail fast.

def checked_incidence(reports, districts, disease):
    """Like ``tmr_incidence.incidence``, but refuse impossible inputs.

    Raise ``ValueError`` before computing anything if:
    - any report has a negative or missing (NaN) case count, or
    - any district has a population of zero or less.
    The message should name the offending report_id(s) or district_id(s), so
    whoever reads the log can find the bad clinic report quickly.
    Otherwise return the same dict as ``tmr_incidence.incidence``.
    """
    # TODO: validate, then call tmr_incidence.incidence(...)
    raise NotImplementedError


# Exercise 2. When is TMR worse than a single replica?

def tmr_reliability(r):
    """Probability that a TMR system (3 replicas + a perfect voter) gives the
    right answer, when each replica independently is right with probability r.
    The voter is right when at least 2 of the 3 replicas are right."""
    # TODO: count the cases "all three right" and "exactly two right".
    raise NotImplementedError


def tmr_break_even():
    """The replica reliability r (0 < r < 1) at which TMR and a single replica
    are equally reliable. Below it, TMR is worse. Solve tmr_reliability(r) == r."""
    # TODO
    raise NotImplementedError


def simulate_tmr(r, trials=20_000, seed=0):
    """Estimate tmr_reliability(r) by simulation: in each trial, each of three
    replicas is right with probability r; count trials where at least two are
    right. Use random.Random(seed) so the result is repeatable."""
    # TODO
    raise NotImplementedError


# Exercise 3. Repair on read.

def read_with_repair(folders, name):
    """Read ``name`` from a list of replica folders written by
    ``checksummed_store.save``. Return the first copy whose checksum verifies.

    Every replica that is corrupted (checksum mismatch) or missing (file or
    checksum file absent) must be rewritten from the good copy, so after the
    call all replicas verify again. If no replica verifies, raise
    ``checksummed_store.CorruptionError``.
    """
    # TODO: hint, checksummed_store.load raises CorruptionError or FileNotFoundError.
    raise NotImplementedError
