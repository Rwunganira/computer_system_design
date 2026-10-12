"""Module 1 worked answers."""

import io

import pandas as pd


def load_reports(csv_text, date_format="%Y-%m-%d"):
    df = pd.read_csv(io.StringIO(csv_text))
    df["week_start"] = pd.to_datetime(df["week_start"], format=date_format)
    df["cases"] = df["cases"].astype(int)
    return df


def compute_incidence(reports, districts, disease, weeks=4):
    latest = reports["week_start"].max()
    recent = reports[(reports["disease"] == disease) & ((latest - reports["week_start"]).dt.days < 7 * weeks)]
    cases = recent.groupby("district_id")["cases"].sum()
    out = districts[["district_id", "district_name", "region", "population"]].copy()
    out["cases"] = out["district_id"].map(cases).fillna(0).astype(int)
    out["rate"] = out["cases"] / out["population"] * 100_000
    out["alert"] = out["rate"] > 10
    out = out.drop(columns="population").reset_index(drop=True)
    out.attrs["latest"] = latest
    return out


def render_page(incidence, disease):
    latest = incidence.attrs["latest"].strftime("%Y-%m-%d")
    html = [f"<h1>{disease.title()} incidence, 4 weeks to {latest}</h1>",
            "<table><tr><th>District</th><th>Cases</th><th>Per 100k</th><th></th></tr>"]
    for r in incidence.itertuples():
        flag = "ALERT" if r.alert else ""
        html.append(f"<tr><td>{r.district_name} ({r.region})</td><td>{r.cases}</td>"
                    f"<td>{r.rate:.1f}</td><td>{flag}</td></tr>")
    html.append("</table>")
    html.append(f"<p>Data through {latest}</p>")
    return "\n".join(html)


def predict_seconds(measured_seconds, measured_n, target_n, exponent):
    return measured_seconds * (target_n / measured_n) ** exponent


def find_duplicate_reports(reports):
    dup = reports.duplicated(subset=["clinic_id", "week_start", "disease"], keep="first")
    return reports.loc[dup, "report_id"].tolist()
