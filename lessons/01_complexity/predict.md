# Predict, then run

1. In `dashboard_v0.py`, if a clinic uploads `23/03/2026` instead of `2026-03-23`, which line fails
   first, and with what error? What would happen if instead the format were `2026/03/23`?
2. `scaling.py` doubles the number of reports each row. Before running it, write down how much slower
   you expect each column to get per row.
3. The naive check takes `t` seconds at 4,000 reports. Using your answer to question 2, how long would
   it take for 1,000,000 reports (a national year of weekly reports at district level)? Convert to hours.
4. The alert threshold of 10 per 100,000 sits inside the HTML loop. Name one future request from an
   epidemiologist that would force you to move it.
