# Capstone. A resilient surveillance system

**Read in the book:** look back over Chapters 1 to 11. No new chapter.

## The idea

Each module so far isolated one idea. Real systems need them all at once, and the hard part is that
failures arrive together: the week the network is bad is also the week a disk fails and someone
tries something they should not. The capstone puts SurveilLite's report intake behind one small
Flask service and runs a scripted "bad week" against it.

`surveillance_system.py` is the service. Clinics `POST /reports`; district officers
`GET /districts/<id>/incidence`. Every accepted delivery is stored as a new record, like an
append-only intake log, and each record is written to two replicas with a SHA-256 checksum, using write-then-rename so a crash never leaves half a file (Module 9).

Three decisions are deliberately left pluggable, because they are where the course's ideas live:

| Function you write | What it must do | Modules |
|---|---|---|
| `accept(message, seen)` | Count each (clinic, sequence number) once, whatever order or how many times it arrives | 4 (at-most-once RPC), 7 (duplicate suppression) |
| `read_verified(replica_paths)` | Return only data whose checksum matches; repair bad replicas; fail fast if none is good | 8 (detection, masking, repair) |
| `authorize(user, action, district_id)` | Clinics submit only for themselves; officers read only their district; deny everything else | 11 (least privilege, fail-safe defaults, complete mediation) |

`NaiveParts` in `surveillance_system.py` is what a first version usually does: accept everything,
trust the first copy, and let any logged-in user do anything. It is not a strawman; each of those
choices is the simplest thing that works on a good day.

## The bad week

`bad_week.py` runs four things at once:

1. **A lost reply.** Clinic C31's phone sends a report, never hears back, and sends it again.
2. **A clinic comes back online.** C32 was offline for three weeks and sends its reports out of order.
3. **Silent corruption.** One replica of one report has a digit changed on disk: 31 cases become 310.
4. **Misuse.** A Hillview officer reads Coastal's data, and a Coastal nurse submits a report as another clinic.

With the naive parts, the dashboard shows 459 cholera cases in Coastal instead of 140 (the retried
report counts twice and the corrupted copy adds 279), and both misuse attempts succeed. An epidemiologist would see a threefold outbreak that did not happen.

## Things to notice

- None of the three functions is long. The design work is deciding *where* each check belongs, which
  is the end-to-end argument from Module 7 applied three times.
- `read_verified` raises an error rather than guessing when no replica is intact. In surveillance,
  a missing number is better than a wrong one.
- Every request goes through `authorize`, including reads. That is complete mediation. Every decision
  is recorded in the audit list, allowed or not.

## Going further

- Make the audit list tamper-evident with a hash chain (Module 11's exercise 2).
- Replace the in-memory `seen` set with a SQLite table so duplicates are still caught after a restart.
  What does that need from Module 9?
- Add a third replica and a voter. When is that worth the extra disk writes?

## Run it

```bash
python lessons/12_capstone/bad_week.py              # naive parts, then yours
python lessons/12_capstone/bad_week.py --solutions  # naive parts, then the worked answers
pytest lessons/12_capstone
```
