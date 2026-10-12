# Course Outline: Computer System Design, in Python

A hands-on companion to Saltzer and Kaashoek, *Principles of Computer System Design* (2009).
Each module takes one chapter's ideas and makes them concrete with a small, runnable Python or Flask
program from public health and data work, followed by short exercises you check yourself with `pytest`.

## Who this is for

A working Python developer who uses Flask and pandas, has an epidemiology background, has read
Guttag's *Introduction to Computation and Programming Using Python*, and is starting Saltzer and
Kaashoek. You already know how to write programs. This course is about how to design *systems*:
things built from many programs, machines and people that must keep working when parts of them fail.

## The running case: a surveillance system that grows

Every module works on the same fictional system, so each new idea lands on code you already know.

- **SurveilLite**, a disease surveillance dashboard. Clinics report weekly case counts (measles,
  cholera, malaria); the dashboard computes incidence per 100,000 by district and flags outbreaks.
- **VaxRecords**, a vaccination records API. Health workers record doses given; the API tracks each
  person's vaccination history and each facility's vaccine stock.

The system starts as one tangled script in Module 1. By the end it is a set of services that
name things carefully, survive crashes, sync offline clinics, and keep patient data safe.

## How each module works

Each module is one folder, `lessons/NN_topic/`, containing:

| File | Purpose |
|---|---|
| `README.md` | The chapter's key ideas in plain language, with the book sections to read alongside |
| `example.py` (or `app.py`) | A runnable example, usually under 150 lines, using only the standard library, Flask, pandas and `requests` |
| `predict.md` | "Predict, then run" prompts: guess what the example will do before running it |
| `exercises.py` | Two to four small exercises with `TODO` markers |
| `test_exercises.py` | Tests that pass once the exercises are done: `pytest lessons/NN_topic` |

Tooling: Python 3.11+, Flask, pandas, requests, pytest, and SQLite (built into Python). No cloud
accounts, Docker or databases to install. Synthetic data generators live in `data/` so no real
patient data is ever used.

---

## Module 0. Setup and the running case

**Goal:** have the environment working and understand the two systems the course builds on.

- Install requirements, run the test suite, generate the synthetic datasets.
- Tour SurveilLite and VaxRecords: what they do, who uses them, what "working" means for each.

**Runnable example:** `data/generate.py` creates a synthetic population, weekly case reports from
40 clinics in 8 districts, and a vaccination register, then prints a summary table with pandas.

**Exercises:** add a new disease to the generator; write a test that checks every report has a
valid district.

---

## Module 1. Complexity (Chapter 1: Systems)

**Learning goals**

- Recognize the signs of complexity: many components, many interconnections, irregularities,
  no short description, and too many people involved.
- Explain the sources the book names: emergent properties, propagation of effects, incommensurate
  scaling, and trade-offs.
- Name the four tools for coping: modularity, abstraction, layering and hierarchy.

**Runnable example:** `lessons/01_complexity/dashboard_v0.py`, a single 200-line Flask script that
reads the CSV, cleans dates, computes incidence and renders HTML all in one function. A companion
`scaling.py` times a naive duplicate-report check (compare every pair) against a set-based one on
1,000, 10,000 and 100,000 reports, showing incommensurate scaling: what was instant at one clinic
takes minutes nationally.

**Exercises**

1. Change the date format in the input file and count how many places in `dashboard_v0.py` break
   (propagation of effects).
2. Refactor the script into three modules (load, compute, present) without changing its output;
   the provided tests confirm behaviour is unchanged.
3. Predict, then measure, the running time of the naive check at 1,000,000 reports.

---

## Module 2. Elements of computer system organization (Chapter 2)

**Learning goals**

- Describe the three fundamental abstractions: memory, interpreters and communication links.
- Understand read/write coherence and why "the last write wins" is not always true.
- See an interpreter as a loop: fetch an instruction, decode it, execute it, repeat.

**Runnable example:** `lessons/02_elements/case_definition.py`, a tiny interpreter for case
definitions written as text, such as `fever AND (rash OR cough) AND age < 15`. It tokenizes the
rule, parses it into a tree, and evaluates it against each patient record. The same rules then run
over a pandas DataFrame, showing one abstraction with two implementations.

**Exercises**

1. Add a `NOT` operator to the interpreter.
2. Add a `WITHIN 14 DAYS OF onset` operator that needs the interpreter to keep state.
3. Write a test showing that two clinics writing the same record without coordination can lose an
   update.

---

## Module 3. Naming (Chapters 2 and 3)

**Learning goals**

- Use the book's vocabulary: name, value, context, binding, and resolution (lookup).
- Distinguish absolute from relative names, and pure from overloaded names.
- Explain why indirection (a name that refers to another name) makes systems easier to change.

**Runnable example:** `lessons/03_naming/patient_resolver.py`. Each clinic gives patients a local
ID ("P-0042" at Clinic A is a different person from "P-0042" at Clinic B). The example builds
naming contexts as dictionaries, resolves `clinic_a/P-0042` to a national registry ID, and shows
how an overloaded name (name plus date of birth as the key) merges two different children. The
Flask part maps URLs like `/districts/<district>/cases` onto these names.

**Exercises**

1. Two regions both have a district called "Central". Make district names unambiguous without
   breaking existing URLs.
2. Add an alias layer so a clinic can be renamed while old reports still resolve.
3. Write a function that detects when one registry ID is bound to records with conflicting
   birth dates.

---

## Module 4. Clients and services (Chapter 4)

**Learning goals**

- Contrast soft modularity (function calls in one program) with enforced modularity (separate
  programs that talk only by messages).
- Explain remote procedure call (RPC) and how it differs from a local call: it can fail, time out,
  or run twice.
- Compare at-least-once, at-most-once and exactly-once semantics.

**Runnable example:** `lessons/04_client_service/`. VaxRecords is split into a Flask service
(`server.py`) and a client (`client.py`) that records doses using `requests`. A flag makes the
server randomly drop responses after saving. Running the naive client with retries records the same
dose twice; adding an idempotency key on each request makes retries safe.

**Exercises**

1. Make the client time out after 2 seconds and retry with exponential backoff.
2. Implement the idempotency-key check on the server, and make the provided duplicate-dose test pass.
3. Explain, in a short comment, why the dashboard crashing no longer takes VaxRecords down with it.

---

## Module 5. Virtualization (Chapter 5)

**Learning goals**

- Understand how threads, virtual memory and bounded buffers enforce modularity inside one computer.
- Recognize a race condition, and fix it with a lock.
- Use sequence coordination (wait and notify) to pass work between threads.

**Runnable example:** `lessons/05_virtualization/lab_pipeline.py`. Several producer threads read lab
result files while consumer threads validate and store them, connected by a bounded buffer the
example builds by hand from a lock and two condition variables (then compares to `queue.Queue`).
A shared positive-result counter without a lock gives the wrong total; the fix is one `with lock:`.

**Exercises**

1. Run the unlocked version until the count is wrong, and write down why.
2. Make producers block when the buffer is full instead of dropping results.
3. Replace threads with processes (`multiprocessing`) and note what changes about shared state.

---

## Module 6. Performance (Chapter 6)

**Learning goals**

- Measure before optimizing: latency, throughput, overhead and the bottleneck.
- Apply the book's general techniques: batching, caching, concurrency, dallying and speculation.
- Reason about queues with Little's law, and about caches with hit rate and working set.

**Runnable example:** `lessons/06_performance/`. A slow dashboard endpoint is profiled with
`cProfile`. Three fixes are measured one at a time: batching inserts into SQLite (`executemany` in
one transaction instead of one commit per row), caching district incidence with
`functools.lru_cache`, and fetching clinic reports concurrently. A small simulation applies
Little's law to patients waiting at a vaccination clinic.

**Exercises**

1. Find the bottleneck in the provided profile output before reading the answer.
2. Add cache invalidation so new reports appear on the dashboard.
3. Use Little's law to size the staffing for a mass vaccination day.

---

## Module 7. Networks (Chapter 7)

**Learning goals**

- Describe the layers: link, network and end-to-end, and what each promises.
- State the end-to-end argument and apply it to a design decision.
- Build reliable delivery on an unreliable channel using sequence numbers, acknowledgements and
  timeouts.

**Runnable example:** `lessons/07_networks/sms_reports.py`. Rural clinics send weekly case counts
over a simulated SMS channel that drops, duplicates and reorders messages. The example first shows
wrong totals at the district office, then adds sequence numbers, acknowledgements, retransmission
and duplicate suppression until totals are correct.

**Exercises**

1. Add a checksum so corrupted messages are detected and resent.
2. Measure how many messages are sent at 10%, 30% and 50% loss.
3. Argue, using the end-to-end argument, whether the SMS gateway or the district office should
   check that totals add up.

---

## Module 8. Fault tolerance (Chapter 8)

**Learning goals**

- Distinguish faults, errors and failures, and compute availability from MTTF and MTTR.
- Use redundancy to detect and mask faults: checksums, replication and voting.
- Design for fail-fast behaviour and for the faults that will certainly happen.

**Runnable example:** `lessons/08_fault_tolerance/`. Case-count files are stored with checksums
that detect silent corruption. Three replicas of the incidence calculator run with one deliberately
faulty, and a voter masks its wrong answer (triple modular redundancy). A short script computes the
availability of the whole dashboard from the availability of its parts.

**Exercises**

1. Add a fail-fast check that refuses impossible inputs (negative cases, population of zero).
2. Calculate when TMR is worse than a single replica, then confirm it by simulation.
3. Make the reader repair a corrupted replica from a good copy.

---

## Module 9. Atomicity (Chapter 9)

**Learning goals**

- Define all-or-nothing and before-or-after atomicity.
- Implement all-or-nothing with shadow copies and with a write-ahead log plus recovery.
- Coordinate concurrent updates with locks, and across services with two-phase commit.

**Runnable example:** `lessons/09_atomicity/`. Recording a dose must update both the patient's
history and the facility's stock. The example crashes the program between the two writes and shows
the inconsistency, then fixes it three ways: a shadow copy (write a temp file, then `os.replace`), a
write-ahead log with a recovery procedure that runs on start-up, and an SQLite transaction. A final
script runs two-phase commit between VaxRecords and a separate stock service.

**Exercises**

1. Insert a crash at every line of the logging version and confirm recovery always restores a
   consistent state (the test does this for you).
2. Show a lost update when two health workers record doses at once, then prevent it with locking.
3. Decide what the coordinator should do if a participant never answers in two-phase commit.

---

## Module 10. Consistency (Chapter 10)

**Learning goals**

- Compare strict consistency with eventual consistency, and know when each is acceptable.
- Understand cache coherence and replica durability.
- Detect and reconcile conflicting updates made while disconnected.

**Runnable example:** `lessons/10_consistency/offline_sync.py`. Two clinic tablets work offline and
sync with the central VaxRecords server when connectivity returns. The example shows a naive
last-writer-wins sync losing a dose, then uses version vectors to detect the conflict and a
domain-specific merge rule (doses are added, never overwritten) to reconcile it.

**Exercises**

1. Write a test that shows last-writer-wins losing data.
2. Implement the version-vector comparison: before, after or concurrent.
3. Decide which dashboard figures can tolerate stale data and which cannot, and justify it.

---

## Module 11. Information security (Chapter 11)

**Learning goals**

- Apply the book's design principles: open design, fail-safe defaults, least privilege, complete
  mediation, economy of mechanism and psychological acceptability.
- Use the guard model: authenticate, authorize, and audit every request.
- Understand what hashing, message authentication codes and encryption each protect.

**Runnable example:** `lessons/11_security/secure_vax_api.py`. VaxRecords gains password login with
salted, slow hashing (`hashlib.scrypt`), role-based authorization (a district officer sees only
their district), an append-only audit log of who read which record, and HMAC-signed requests between
services. The starting version contains a real bug: changing the ID in `/patients/<id>` shows anyone's
record.

**Exercises**

1. Find and fix the record-access bug, then write a test that would have caught it.
2. Make the audit log tamper-evident by chaining entry hashes.
3. Write a one-page threat model for VaxRecords: assets, adversaries and the controls that address
   each.

---

## Capstone. A resilient surveillance system

Bring the modules together: SurveilLite and VaxRecords as separate services with clear names,
idempotent RPC, atomic dose recording, offline sync, tolerance of a failed replica, and
authenticated, audited access. A scripted "bad week" (a clinic goes offline, a disk corrupts a file,
a message is duplicated, an unauthorized request arrives) checks that the dashboard still reports
correct numbers.

## Suggested pace

One module per week alongside the matching chapter, with the capstone over two weeks: about
14 weeks in total. Modules 1 to 6 follow the printed book (Part I); modules 7 to 11 follow the
chapters published online (Part II).

## Next steps after this outline

1. Agree on the outline, the running case, and the module format.
2. Build Module 0 and the synthetic data generator.
3. Write modules in order, each as its own pull request with passing tests.
