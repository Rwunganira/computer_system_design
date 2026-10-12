# Module 10. Consistency

**Goal:** know when every reader must see the latest write and when "eventually" is good enough,
and keep offline clinics from silently losing doses when they sync.

**Read in the book:** Chapter 10, *Consistency* (part of the online Part II): constraints across
replicas, cache coherence, durable storage on replicas, and reconciling replicas after disconnection.

## Strict and eventual consistency

When there is one copy of the data, every read sees the last write. Once you make copies (a cache in
front of the dashboard, a read replica of the VaxRecords database, a tablet in a clinic with no
signal) you must decide what readers may see. The book contrasts two answers:

- **Strict consistency:** every read returns the result of the most recent write, as if there were a
  single copy. Simple to reason about, but it costs coordination: a write is not finished until the
  replicas agree, and if a replica cannot be reached you must either wait or refuse.
- **Eventual consistency:** replicas may disagree for a while, but if updates stop they converge to
  the same value. Reads are fast and work when disconnected; the price is that a reader can see
  stale data, and the system needs a rule for combining updates made in different places.

Neither is "correct". The question is what a stale answer costs. A SurveilLite incidence map that is
an hour old leads to the same decision as a fresh one. A nurse checking whether a child already had
MCV1 before giving it cannot safely act on stale data, or must at least be told the data may be
stale. Exercise 4 asks you to make these calls.

## Cache coherence and replica durability

A **cache** is a replica whose job is speed. It is **coherent** if reads through it behave as if
there were no cache. The book's tools are familiar from web work: invalidate the cached copy on
every write, or bound staleness with a time-to-live and accept that window. If SurveilLite caches
district totals for five minutes, that is an explicit, bounded eventual-consistency promise.

Replicas also exist for **durability**: several copies so a lost disk does not lose doses. The same
question returns in a new form: after a write, how many replicas must have it before you tell the
health worker "saved"?

## Disconnected operation

VaxRecords runs on tablets in clinics that are offline for days. Each tablet keeps a full copy of the
records it needs, health workers keep recording doses, and the tablet syncs when it reconnects. Now
two replicas can change the same record independently. The book calls this the reconciliation
problem, and it has two parts: **detect** that updates conflict, then **resolve** them.

**Last-writer-wins (LWW)** skips detection: each record carries a timestamp and the later one
replaces the earlier one wholesale. It is easy, and it loses data. If tablet A and tablet B each add a
dose to the same child, one tablet's whole record wins and the other dose vanishes, with no error.
Device clocks make it worse, because "later" is decided by whichever cheap clock runs fast.

**Version vectors** detect conflicts without trusting clocks. Each replica counts its own updates;
the vector `{"server": 1, "tablet-A": 2}` means "I have seen the server's first update and tablet A's
first two". Comparing two vectors gives one of four answers:

| Comparison | Meaning | Action |
|---|---|---|
| equal | same history | nothing to do |
| before / after | one has seen everything the other has | take the newer one |
| concurrent | each has an update the other lacks | reconcile |

**Resolving** a concurrent update needs knowledge of the domain, not of the system. For doses the
rule is simple: a dose, once given, stays given. Doses form a *grow-only set*, so the merge is a
union, and the merged vector is the slot-by-slot maximum. Because union is commutative and
idempotent, replicas can sync in any order, any number of times, and still converge. Not every
field is that easy (a corrected birth date needs a person to decide), which is why good designs
shape their data so most updates are additions.

## Run the example

```bash
python lessons/10_consistency/offline_sync.py
```

It runs the same scenario twice: two tablets each record a dose for the same child while offline.
With last-writer-wins one dose is lost; with version vectors and the grow-only merge both survive.
Answer `predict.md` first, then do the exercises:

```bash
pytest lessons/10_consistency
```
