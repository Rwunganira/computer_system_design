"""A first look at the synthetic data behind SurveilLite and VaxRecords."""

from course.data import DISTRICTS, case_reports, clinics, population, vaccinations


def main():
    reports = case_reports()
    people = population()
    doses = vaccinations(people)

    print(f"{len(DISTRICTS)} districts, {len(clinics())} clinics, {reports.week_start.nunique()} weeks of reports")
    print(f"{len(people):,} children, {len(doses):,} vaccine doses\n")

    print("Total cases by disease:")
    print(reports.groupby("disease").cases.sum().to_string(), "\n")

    weekly = (reports[reports.disease == "cholera"]
              .groupby(["district_id", "week_start"]).cases.sum()
              .unstack("week_start"))
    print("Cholera cases by district and week (spot anything?):")
    print(weekly.to_string(header=[str(d)[5:] for d in weekly.columns]))


if __name__ == "__main__":
    main()
