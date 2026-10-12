# Predict, then run

Answer each question in a sentence before running the examples.

1. `slow_dashboard.py` fetches 40 clinic reports (20 ms each), saves 1,440 rows to SQLite with a
   commit after each one, and filters a pandas DataFrame 120 times. Rank the three by how much
   time you expect each to take. Then read the profile: were you right?
2. In `dashboard_fixes.py`, fetching with 10 threads instead of one at a time: will it be about
   10 times faster, 40 times faster, or barely faster? Does each single fetch get faster?
3. The page needs incidence for 40 clinics x 3 diseases = 120 lookups, but there are only 8
   districts. What hit rate will `lru_cache` report? What happens to the hit rate if the page
   showed each district once instead of each clinic?
4. In `clinic_queue.py`, 90 children an hour each need 2.5 minutes. With 4 vaccinators the
   utilisation is 94%. Do you expect the average time inside to be close to 2.5 minutes, about
   double, or much more? What about with 3 vaccinators?
