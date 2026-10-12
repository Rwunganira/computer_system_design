"""Triple modular redundancy (TMR) for the incidence calculator.

Three replicas compute cholera incidence per 100,000 by district. One replica
has a fault: it reads a stale copy of the data that stops before the outbreak.
A voter compares the three answers district by district and takes the majority,
so the faulty replica's wrong answer is masked.
"""

from collections import Counter

from course.data import DISTRICTS, case_reports


class NoMajority(Exception):
    """The replicas disagree and no value has a majority."""


def incidence(reports, districts, disease):
    """Total cases of ``disease`` per 100,000 people, as {district_id: value}."""
    cases = reports[reports.disease == disease].groupby("district_id").cases.sum()
    pop = districts.set_index("district_id").population
    rates = cases.reindex(pop.index, fill_value=0) / pop * 100_000
    return {d: round(float(v), 2) for d, v in rates.items()}


def healthy_replica(reports, districts, disease):
    return incidence(reports, districts, disease)


def stale_replica(reports, districts, disease):
    """Faulty: its copy of the data was last synced in week 6."""
    weeks = sorted(reports.week_start.unique())
    return incidence(reports[reports.week_start < weeks[6]], districts, disease)


def vote(answers):
    """Majority vote, district by district, over a list of {district: value} dicts."""
    result = {}
    for district in answers[0]:
        value, count = Counter(a[district] for a in answers).most_common(1)[0]
        if count <= len(answers) // 2:
            raise NoMajority(f"{district}: {[a[district] for a in answers]}")
        result[district] = value
    return result


def show(label, answer):
    print(f"   {label:<10} S-COA = {answer['S-COA']:7.2f}   N-CEN = {answer['N-CEN']:6.2f}")


def main():
    reports = case_reports()
    replicas = {"A": healthy_replica, "B": stale_replica, "C": healthy_replica}

    print("Cholera incidence per 100,000 from three replicas (B has a stale data copy):")
    answers = {name: fn(reports, DISTRICTS, "cholera") for name, fn in replicas.items()}
    for name, answer in answers.items():
        show(f"replica {name}", answer)

    print("\nWith only replica B, the dashboard would miss the S-COA outbreak.")
    voted = vote(list(answers.values()))
    print("Voter output (majority of A, B, C):")
    show("voted", voted)
    outvoted = [n for n, a in answers.items() if a != voted]
    print(f"   Fault masked. Replicas outvoted: {outvoted} (log this: a masked fault still needs repair)")

    print("\nThe limit of voting: a common-mode fault. B and C now share the same stale copy:")
    answers = [healthy_replica(reports, DISTRICTS, "cholera"),
               stale_replica(reports, DISTRICTS, "cholera"),
               stale_replica(reports, DISTRICTS, "cholera")]
    show("voted", vote(answers))
    print("   The majority is wrong, and the voter confidently reports it.")
    print("   Replicas must fail independently for voting to help.")


if __name__ == "__main__":
    main()
