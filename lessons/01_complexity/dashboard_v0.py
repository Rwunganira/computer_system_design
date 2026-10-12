"""SurveilLite, version 0: everything in one place.

This is deliberately how many real dashboards start. It works, but loading,
cleaning, computing and presenting are tangled together in one function.
Read it with Chapter 1 in mind: count the places that know the date format,
the column names, or the shape of the HTML.

    python lessons/01_complexity/dashboard_v0.py           # print the page
    python lessons/01_complexity/dashboard_v0.py --serve   # open http://127.0.0.1:5000
"""

import csv
import io
import sys
from datetime import datetime

from flask import Flask

from course.data import DISTRICTS, case_reports

app = Flask(__name__)


def sample_csv():
    """The weekly reports as CSV text, the way clinics would upload them."""
    return case_reports().to_csv(index=False)


def build_page(csv_text, disease="cholera"):
    rows = list(csv.DictReader(io.StringIO(csv_text)))

    # Find the latest week. (Knows the date format.)
    latest = max(datetime.strptime(r["week_start"], "%Y-%m-%d") for r in rows)

    # Sum cases per district for the last four weeks. (Knows the date format again,
    # and the column names, and the disease spelling.)
    totals = {}
    for r in rows:
        week = datetime.strptime(r["week_start"], "%Y-%m-%d")
        if r["disease"] == disease and (latest - week).days < 28:
            totals[r["district_id"]] = totals.get(r["district_id"], 0) + int(r["cases"])

    # Incidence per 100,000, with population looked up inline.
    html = [f"<h1>{disease.title()} incidence, 4 weeks to {latest.strftime('%Y-%m-%d')}</h1>",
            "<table><tr><th>District</th><th>Cases</th><th>Per 100k</th><th></th></tr>"]
    for d in DISTRICTS.itertuples():
        cases = totals.get(d.district_id, 0)
        rate = cases / d.population * 100_000
        flag = "ALERT" if rate > 10 else ""  # threshold buried in presentation code
        html.append(f"<tr><td>{d.district_name} ({d.region})</td><td>{cases}</td>"
                    f"<td>{rate:.1f}</td><td>{flag}</td></tr>")
    html.append("</table>")
    # The footer needs the date again, so the format appears a fourth time.
    html.append(f"<p>Data through {latest.strftime('%Y-%m-%d')}</p>")
    return "\n".join(html)


@app.route("/")
def index():
    return build_page(sample_csv())


if __name__ == "__main__":
    if "--serve" in sys.argv:
        app.run(debug=True)
    else:
        print(build_page(sample_csv()))
