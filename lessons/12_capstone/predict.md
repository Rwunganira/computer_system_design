# Predict, then run

1. With the naive parts, the true Coastal cholera total is 140. Work out what the dashboard will show
   before running `bad_week.py`. (Hint: one report is counted twice and one copy is corrupted.)
2. C32's reports arrive as sequence numbers 3, 1, 2. Should a design that rejects anything below the
   highest sequence number seen so far accept all three? What would it get wrong?
3. If both replicas of a report are corrupted, should the dashboard show the district total without
   that report, or an error? Argue for one from an epidemiologist's point of view.
4. The audit list records eight entries for the bad week. List them before checking.
