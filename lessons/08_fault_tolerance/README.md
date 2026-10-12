# Module 8. Fault tolerance

**Goal:** expect parts of SurveilLite and VaxRecords to fail, detect the failures quickly, and use
redundancy so that a fault in one part does not become a wrong number on the dashboard.

**Read in the book:** Chapter 8, "Fault Tolerance: Reliable Systems from Unreliable Components".

## Faults, errors and failures

The book separates three things that everyday speech lumps together:

- A **fault** is the underlying defect: a flipped bit on a disk, a bug, a stale copy of the data.
- An **error** is what the fault does when it is activated: a wrong value inside the system.
- A **failure** is when the system as a whole stops doing what its specification promises: the
  dashboard shows a cholera incidence of 8 per 100,000 in Coastal district when it is really 252.

Epidemiologists will recognise the shape: exposure, infection, disease. Not every fault becomes an
error, and not every error becomes a failure. Fault tolerance is about breaking that chain, and the
most important break is to **detect** an error before it propagates. A **latent** fault (the bad
byte sitting unread on disk) is the dangerous kind, because nothing tells you it is there.

## Fail fast

A component that detects something wrong should stop and say so, rather than carry on and produce
a plausible but wrong answer. This is **fail-fast** design. A negative case count or a district with
a population of zero is not something to round, clip or skip silently: it means some clinic
report or some table is broken, and the incidence computed from it cannot be trusted. Refusing the
input, loudly, with the report_id in the message, is the useful response. Exercise 1 does this.

## Redundancy: detect, then mask

All fault tolerance comes down to redundancy, used in one of two ways.

- **Error detection.** Store a little extra information that lets you notice damage. A SHA-256
  **checksum** saved next to each case-count file costs 64 bytes, and turns a silent bit flip into a
  `CorruptionError`. `checksummed_store.py` shows the same flipped bit read twice: once trusted
  (a wrong total, no warning) and once verified (an exception). Detection alone does not give you
  the right answer, but it stops you publishing the wrong one.
- **Error masking.** Keep enough redundant copies that you can still produce the right answer.
  With two checksummed replicas, a reader that finds one bad copy reads the other one, and
  (Exercise 3) rewrites the bad one from it. Repairing on read matters: if you only mask, faults
  accumulate silently until every copy is bad.

**N-modular redundancy** masks faults in computation, not just storage. In `tmr_incidence.py` three
replicas compute incidence and a **voter** takes the majority answer per district. One replica is
running on a stale data copy and misses the outbreak; the voter outvotes it. Voting only works if
replicas fail **independently**. The second half of the example gives two replicas the same stale
data (a **common-mode fault**): the majority is now wrong and the voter reports it with full
confidence. Running three copies of the same buggy code is the classic common-mode fault.

If each replica is right with probability r, TMR is right when at least two are right. Exercise 2
asks you to work out when that is *worse* than a single replica, and confirm it by simulation.

## Availability from MTTF and MTTR

Components fail and get repaired, again and again. With **MTTF** (mean time to failure) and **MTTR**
(mean time to repair):

    availability = MTTF / (MTTF + MTTR)

Parts in **series** (the dashboard needs power *and* the network *and* the app server *and* the
database) multiply their availabilities, so the whole is less available than its weakest part.
Parts in **parallel** (two network links, either is enough) are down only when all are down:
`1 - (1 - a1)(1 - a2)`. `availability.py` shows a dashboard down about ten days a year become one
down about a day and a half a year by duplicating the two cheapest, least reliable parts. Note the
other lever: shortening MTTR (a spare on the shelf, a runbook, an alert) improves availability as
surely as lengthening MTTF, and is often cheaper.

These formulas assume independent failures. A shared power supply, a shared bug, or a shared
administrator who makes the same mistake on both servers all break that assumption.

## Design for the faults that will happen

The book's advice, applied to the running case:

- Assume every disk, link and clinic report will eventually be wrong. Check, do not trust.
- Make faults visible: log every masked fault, because a masked fault is a lost safety margin.
- Keep MTTR short: repair automatically where you can (repair on read), alert where you cannot.
- Look for the common modes: same code, same data source, same power, same person.

## Run the examples

From the repository root:

```bash
.venv/bin/python lessons/08_fault_tolerance/checksummed_store.py   # silent corruption, detected
.venv/bin/python lessons/08_fault_tolerance/tmr_incidence.py       # three replicas and a voter
.venv/bin/python lessons/08_fault_tolerance/availability.py        # series and parallel availability
.venv/bin/pytest lessons/08_fault_tolerance                         # fails until you do the exercises
```
