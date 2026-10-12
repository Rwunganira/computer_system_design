# Computer System Design, in Python

An interactive course that follows Saltzer and Kaashoek's *Principles of Computer System Design*,
one chapter at a time, with runnable Python and Flask examples drawn from public health and data work.

Every module works on the same two fictional systems: **SurveilLite**, a disease surveillance
dashboard, and **VaxRecords**, a vaccination records API. All data is synthetic.

**Read it as a website:** https://rwunganira.github.io/computer_system_design/

## Start here

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m course.data          # write the synthetic datasets to data/generated/
```

Then open [`lessons/00_setup/README.md`](lessons/00_setup/README.md).

## Modules

| Module | Book chapter | You build |
|---|---|---|
| [0. Setup](lessons/00_setup) | | A tour of the synthetic data; find the hidden cholera outbreak |
| [1. Complexity](lessons/01_complexity) | 1 | Refactor a tangled dashboard; watch an O(n²) check fail to scale |
| [2. Elements](lessons/02_elements) | 2 | An interpreter for case-definition rules |
| [3. Naming](lessons/03_naming) | 2, 3 | A patient identifier resolver across clinics |
| [4. Clients and services](lessons/04_client_service) | 4 | VaxRecords as a service, with safe retries via idempotency keys |
| [5. Virtualization](lessons/05_virtualization) | 5 | A threaded lab-result pipeline with a bounded buffer |
| [6. Performance](lessons/06_performance) | 6 | Profile and speed up the dashboard; Little's law at a clinic |
| [7. Networks](lessons/07_networks) | 7 | Reliable SMS case reporting over a lossy channel |
| [8. Fault tolerance](lessons/08_fault_tolerance) | 8 | Checksums, triple modular redundancy and availability |
| [9. Atomicity](lessons/09_atomicity) | 9 | Crash-safe dose recording: shadow copies, logs, two-phase commit |
| [10. Consistency](lessons/10_consistency) | 10 | Offline clinic tablets that sync without losing doses |
| [11. Security](lessons/11_security) | 11 | Authentication, authorization and a tamper-evident audit log |
| [Capstone](lessons/12_capstone) | 1 to 11 | A surveillance service that survives a scripted bad week |

The full plan, with learning goals per module, is in [`COURSE_OUTLINE.md`](COURSE_OUTLINE.md).

## How a module works

Each folder has a `README.md` with the chapter's ideas, runnable examples, `predict.md` questions to
answer before running them, and `exercises.py` with `TODO`s. Check your work with:

```bash
pytest lessons/01_complexity                      # your exercises
COURSE_SOLUTIONS=1 pytest lessons/01_complexity   # the worked answers in solutions.py
```

Try the exercises before opening `solutions.py`.

## Building the website

The website is generated from the lessons, so each module's README, examples, exercises and
solutions stay the single source. To preview it locally:

```bash
pip install -r requirements-site.txt
python scripts/build_site.py --serve   # http://127.0.0.1:8000
```

Every push to `main` publishes it to GitHub Pages.
