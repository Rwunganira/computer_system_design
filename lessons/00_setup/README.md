# Module 0. Setup and the running case

**Goal:** get the environment working and meet the two systems the rest of the course builds on.

## Set up

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                   # makes the shared `course` package importable
python -m course.data              # writes the synthetic datasets to data/generated/
pytest lessons/00_setup            # fails until you do this module's exercises
```

## The running case

Every module works on the same two fictional systems, so each new idea lands on code you already know.

**SurveilLite** is a disease surveillance dashboard. Forty clinics in eight districts report weekly
counts of measles, cholera and malaria. The dashboard computes incidence per 100,000 people by
district and flags outbreaks. There is a cholera outbreak hidden in the synthetic data: find it in
the exercises.

**VaxRecords** is a vaccination records API. Health workers record each dose they give; the API keeps
each child's vaccination history and each clinic's stock.

All the data comes from `course/data.py`. It is synthetic, generated from a fixed seed, and safe to
share. Read that file now: it is short, and you will use its functions in almost every module.

| Function | Returns |
|---|---|
| `DISTRICTS` | 8 districts in 2 regions, with population |
| `clinics()` | 40 clinics, 5 per district |
| `case_reports()` | one row per clinic, week and disease, with a case count |
| `population(n)` | `n` synthetic children with names, birth dates and districts |
| `vaccinations(people)` | the doses those children received |

## What "working" means

Before you design a system, decide what it must do and what failure looks like. For SurveilLite, a
wrong number is worse than a slow page: an epidemiologist may act on it. For VaxRecords, losing a
dose record means a child may be vaccinated twice, or not at all. Keep these in mind; the book's
chapters on fault tolerance, atomicity and consistency are about exactly these failures.

## How each module works

Each module folder has:

- `README.md`: the chapter's ideas in plain language, and what to read in the book.
- one or more runnable examples. Run them, read them, change them.
- `predict.md`: questions to answer *before* you run the examples.
- `exercises.py`: functions marked `TODO` for you to complete.
- `test_exercises.py`: run `pytest lessons/<module>` until it passes.
- `solutions.py`: one worked answer. Check it with `COURSE_SOLUTIONS=1 pytest lessons/<module>`.

## Run the example

```bash
python lessons/00_setup/tour.py
```
