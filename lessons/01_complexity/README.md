# Module 1. Complexity

**Read in the book:** Chapter 1, "Systems".

## The idea

Chapter 1 argues that the main enemy of a system designer is complexity, and that complexity rarely
arrives all at once. A dashboard starts as one script that one person understands. Then a second
data source arrives, a new disease, a district that reports late, a second analyst. Nothing was
designed badly; it simply grew. The book's point is that you can recognise the signs early and that
a small set of techniques keeps growth under control.

### Signs of complexity

The book lists symptoms you can check for in your own code:

- **Many components** and **many interconnections** between them.
- **Irregularities**: special cases ("district X reports on Tuesdays", "this clinic sends totals, not counts").
- **No short description**: you cannot explain what the system does in a paragraph.
- **A large team**, or too many people with partial understanding.

### Where complexity comes from

- **Emergent properties.** Behaviour that no single part has. Each clinic's report is fine; together
  they double-count a district because two clinics share a catchment.
- **Propagation of effects.** A small change in one place forces changes far away. Change the date
  format in the upload and three unrelated lines of `dashboard_v0.py` break.
- **Incommensurate scaling.** Parts of the system grow at different rates. A duplicate check that
  compares every pair of reports is instant for one clinic and takes hours for a country.
- **Trade-offs.** Every design choice gives something up: speed for accuracy, flexibility for simplicity.

### Coping with complexity

The rest of the book elaborates four techniques. You will use all of them in this course.

| Technique | Meaning | In SurveilLite |
|---|---|---|
| **Modularity** | Split the system into parts that interact only through defined interfaces | load / compute / present as separate functions |
| **Abstraction** | Hide how a module works behind what it does | `compute_incidence()` without knowing it uses pandas |
| **Layering** | Build each layer only on the one below it | HTML on incidence tables on parsed reports on CSV |
| **Hierarchy** | Group modules into larger modules | clinic, district, region, nation |

The book adds a fifth habit, **design for iteration**: you will not get the design right first time, so
make it cheap to change. That is exactly what modularity buys you in exercise 2.

## The examples

`dashboard_v0.py` is SurveilLite as one function. It works. Read it and count how many places know
the date format (three), the column names, the alert threshold and the HTML layout. Each of those is
an interconnection that a future change must find.

`scaling.py` times two duplicate-report checks. The naive one compares every pair; the set-based one
remembers keys it has seen. Watch the naive column grow four times for every doubling of the input.

## Exercises

1. **Propagation of effects.** Write `load_reports()` so the date format lives in exactly one place,
   and a new upload format is a one-argument change.
2. **Modularity.** Split `build_page()` into `compute_incidence()` and `render_page()`. The tests check
   that your modular version produces exactly the same HTML as version 0.
3. **Incommensurate scaling.** Predict the naive check's running time at one million reports, then write
   a duplicate finder that handles 600,000 rows in a few seconds.

## Run it

```bash
python lessons/01_complexity/dashboard_v0.py
python lessons/01_complexity/dashboard_v0.py --serve   # then open http://127.0.0.1:5000
python lessons/01_complexity/scaling.py
pytest lessons/01_complexity
```
