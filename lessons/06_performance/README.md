# Module 6. Performance

**Goal:** make SurveilLite's dashboard fast the disciplined way: measure, find the bottleneck, fix
that one thing, measure again. Then use Little's law to plan a mass vaccination day.

**Read in the book:** Chapter 6, *Performance*: performance metrics, the iterative approach to
design for performance, reducing latency, overlapping latency with concurrency, batching, dallying
and speculation, the multilevel memory and caching, and scheduling.

## The words the book uses

- **Latency**: how long one request takes, start to finish. The epidemiologist clicking "refresh"
  feels latency.
- **Throughput**: how many requests are finished per unit time. The district office uploading 40
  clinic reports at once cares about throughput.
- **Overhead**: work that is not the job itself: a network round trip, a disk flush, a function
  call. Often the overhead per item dwarfs the item.
- **Bottleneck**: the one stage that limits the whole. Speeding up anything else barely helps.
  Speeding up the bottleneck moves the bottleneck somewhere else.

The book's method is iterative: **measure** first, find the bottleneck, apply one technique, measure
again, and stop when the system is fast enough. Guessing is a bad substitute for measuring, because
the bottleneck is rarely where a programmer expects. In the example the profile says SQLite commits
cost more than everything else, and pandas, which looks expensive, hardly registers.

## The general techniques

Once you know where the time goes, the book offers a short list of tools that work in every layer
of a system, from the processor to the network:

- **Batching**: pay a fixed overhead once for many items. One transaction for 1,440 inserts instead
  of 1,440 transactions; one SQL query for all of a district's doses instead of one per child.
- **Caching**: keep a copy of a result close by, so you do not compute or fetch it again. A cache is
  judged by its **hit rate**. It works when requests have locality, that is a small **working set**
  used again and again. A dashboard showing 40 clinics in 8 districts needs only 24 incidence
  figures, used 120 times. The price is that the copy can be stale: a cache needs an
  **invalidation** rule, or new outbreak reports never reach the page.
- **Concurrency**: overlap waits. A fetch from a rural clinic spends nearly all its time waiting on
  the network. Ten waits at once take about as long as one. Latency per fetch is unchanged;
  throughput goes up tenfold.
- **Dallying**: delay work in the hope that it becomes unnecessary or can be batched. Write
  dose records to a buffer and flush every few seconds.
- **Speculation**: do work before it is asked for, betting it will be. Precompute this week's
  incidence table when the last clinic reports, before anyone opens the dashboard.

## Queues and Little's law

Every service with a waiting line is a queue: requests at a web server, children at a vaccination
clinic. **Little's law** relates three averages in any stable queue:

    N  =  X  x  R
    people inside = throughput (per unit time) x time each spends inside

It needs no assumption about how arrivals or service are distributed, so it is a quick sanity
check on any capacity plan. Apply it to the vaccinators alone: 90 children an hour, 2.5 minutes
each, means 3.75 vaccinators busy on average. With 4 vaccinators each is 94% **utilised**, and the
simulation shows what queueing theory predicts: as utilisation approaches 1, waiting time grows
very fast, and above 1 the queue grows without limit. Plan for a utilisation well below 1.

## In the running case

- **SurveilLite**: the dashboard refresh fetches 40 clinic reports, stores them, and computes
  incidence. `slow_dashboard.py` does all three naively; `dashboard_fixes.py` applies concurrency,
  batching and caching one at a time and checks each gives the same page.
- **VaxRecords**: on a mass vaccination day, the API and the clinic both become queues. The
  exercises use Little's law to staff it.

## Exercises

In `exercises.py`:

1. Read a cProfile table, decide where the bottleneck is, then write `bottleneck()` to find it.
2. Write `IncidenceCache`, which invalidates only the entries a new report changes.
3. Use Little's law to size the waiting area and the number of vaccinators.
4. Write `fetch_all()` to fetch clinic reports concurrently.

## Run the examples

```bash
python lessons/06_performance/slow_dashboard.py    # profile the slow refresh (~5 s)
python lessons/06_performance/dashboard_fixes.py   # measure each fix (~5 s)
python lessons/06_performance/clinic_queue.py      # Little's law simulation
pytest lessons/06_performance
```

Timings depend on your machine and disk. The ratios matter, not the exact numbers.
