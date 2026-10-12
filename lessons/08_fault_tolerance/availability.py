"""Availability of the SurveilLite dashboard from its parts' MTTF and MTTR.

Availability = MTTF / (MTTF + MTTR): the fraction of time a component is up.
Parts in series (all needed) multiply their availabilities. Redundant parts in
parallel (any one is enough) are down only when all of them are down.
"""

from math import prod

HOURS_PER_YEAR = 365 * 24


def availability(mttf, mttr):
    """Fraction of time up, from mean time to failure and mean time to repair (same units)."""
    return mttf / (mttf + mttr)


def series(*parts):
    """All parts are needed: the system is up only when every part is up."""
    return prod(parts)


def parallel(*parts):
    """Any one part is enough: the system is down only when every part is down."""
    return 1 - prod(1 - a for a in parts)


def downtime_hours_per_year(a):
    return (1 - a) * HOURS_PER_YEAR


# MTTF and MTTR in hours. Invented but plausible numbers for a district server room.
COMPONENTS = {
    "power supply": (500, 1),
    "district network link": (300, 6),
    "app server (Flask)": (720, 2),
    "database server": (2_000, 4),
}


def report(label, a):
    print(f"   {label:<28} {a:.5f}   {downtime_hours_per_year(a):7.1f} h down per year")


def main():
    parts = {name: availability(*v) for name, v in COMPONENTS.items()}
    print("Each component on its own:")
    for name, a in parts.items():
        report(name, a)

    print("\nThe dashboard needs all four (series):")
    single = series(*parts.values())
    report("dashboard", single)
    print("   Worse than any single part: every part in series adds its downtime.")

    print("\nAdd redundancy where it is cheapest: two network links, two app servers:")
    link = parallel(parts["district network link"], parts["district network link"])
    app = parallel(parts["app server (Flask)"], parts["app server (Flask)"])
    report("2 links in parallel", link)
    report("2 app servers in parallel", app)
    redundant = series(parts["power supply"], link, app, parts["database server"])
    report("dashboard, with redundancy", redundant)

    print("\nThe weakest remaining part now dominates. Halving the power MTTR (1 h -> 0.5 h):")
    report("+ faster power repair",
           series(availability(500, 0.5), link, app, parts["database server"]))
    print("\nAssumes independent failures. One shared power supply under both app servers")
    print("is a common-mode fault that parallel redundancy does not cover.")


if __name__ == "__main__":
    main()
