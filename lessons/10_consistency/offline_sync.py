"""Two clinic tablets edit one child's record offline, then sync with VaxRecords.

Round 1 syncs with last-writer-wins (LWW): the record with the later timestamp
replaces the other wholesale, and a dose silently disappears.
Round 2 attaches a version vector to each record, so the server can tell
"this update already includes mine" from "we both changed it independently".
Concurrent updates are reconciled with a domain rule: doses are a grow-only
set, so merging is a union. Nothing is ever overwritten.
"""

import copy

from course.data import population, vaccinations


# --- Version vectors --------------------------------------------------------
# A version vector maps replica name -> how many updates that replica has made.
# {"server": 1, "tablet-A": 2} means "I have seen the server's first update and
# tablet A's first two". Missing entries count as 0.

def dominates(a, b):
    """True if vector ``a`` has seen everything ``b`` has (a >= b in every slot)."""
    return all(a.get(k, 0) >= n for k, n in b.items())


def merged_vector(a, b):
    """Slot-by-slot maximum: a vector that has seen everything either has seen."""
    return {k: max(a.get(k, 0), b.get(k, 0)) for k in a.keys() | b.keys()}


# --- Replicas ---------------------------------------------------------------

class Replica:
    """One copy of the record: the central server or an offline tablet."""

    def __init__(self, name, record, clock_skew=0):
        self.name = name
        self.record = copy.deepcopy(record)
        self.clock_skew = clock_skew  # minutes this device's clock is off by

    def record_dose(self, vaccine, day, clinic_id, now):
        """A health worker records a dose. ``now`` is true time in minutes."""
        self.record["doses"].add((vaccine, day, clinic_id))
        self.record["updated_at"] = now + self.clock_skew  # what *this* clock says
        vv = self.record["vv"]
        vv[self.name] = vv.get(self.name, 0) + 1


def lww_sync(server, tablet):
    """Last-writer-wins: keep whichever whole record has the later timestamp."""
    if tablet.record["updated_at"] > server.record["updated_at"]:
        outcome = "tablet's timestamp is later: its whole record replaces the server's"
        server.record = copy.deepcopy(tablet.record)
    else:
        outcome = "server's timestamp is later: tablet's record discarded"
    tablet.record = copy.deepcopy(server.record)  # tablet downloads the result
    return outcome


def vv_sync(server, tablet):
    """Version-vector sync: detect concurrency, merge with the grow-only rule."""
    mine, theirs = server.record["vv"], tablet.record["vv"]
    if dominates(mine, theirs):
        outcome = "server already has it"
    elif dominates(theirs, mine):
        outcome = "tablet is newer: take it"
        server.record = copy.deepcopy(tablet.record)
    else:
        outcome = "CONCURRENT: merge doses (union)"
        server.record["doses"] |= tablet.record["doses"]
        server.record["vv"] = merged_vector(mine, theirs)
    tablet.record = copy.deepcopy(server.record)
    return outcome


# --- The scenario -----------------------------------------------------------

def starting_record():
    """A synthetic child whose last two doses have not been entered yet."""
    people = population()
    child = people.iloc[0]
    doses = vaccinations(people)
    doses = doses[doses.person_id == child.person_id].sort_values("dose_date")
    given = {(d.vaccine, str(d.dose_date), d.clinic_id) for d in doses.itertuples()}
    pending = sorted(given, key=lambda d: d[1])[-2:]  # the two most recent doses
    record = {"person_id": child.person_id, "doses": given - set(pending),
              "updated_at": 0, "vv": {"server": 1}}
    return record, pending


def run(sync):
    """Both tablets download the record, go offline, each record one dose, then sync."""
    record, (dose_a, dose_b) = starting_record()
    server = Replica("server", record)
    # Tablet B's clock runs 30 minutes slow: common on cheap devices with no network time.
    tablet_a = Replica("tablet-A", record)
    tablet_b = Replica("tablet-B", record, clock_skew=-30)

    tablet_a.record_dose(*dose_a, now=600)   # 10:00 true time
    tablet_b.record_dose(*dose_b, now=615)   # 10:15 true time, but its clock says 09:45

    outcomes = [sync(server, tablet_a), sync(server, tablet_b)]
    expected = record["doses"] | {dose_a, dose_b}
    return server, expected, outcomes


def show(title, sync):
    print(f"== {title}")
    server, expected, outcomes = run(sync)
    for name, outcome in zip(["tablet-A", "tablet-B"], outcomes):
        print(f"  sync {name}: {outcome}")
    got = server.record["doses"]
    print(f"  doses recorded on tablets + server: {len(expected)}   doses on server: {len(got)}")
    for vaccine, day, clinic in sorted(expected - got):
        print(f"  LOST: {vaccine} given {day} at {clinic}")
    if got == expected:
        print(f"  nothing lost; version vector now {dict(sorted(server.record['vv'].items()))}")
    print()


def main():
    record, pending = starting_record()
    print(f"Child {record['person_id']} has {len(record['doses'])} doses on the server.")
    print(f"Offline, tablet A records {pending[0][0]} and tablet B records {pending[1][0]}.\n")
    show("Round 1: last-writer-wins by device timestamp", lww_sync)
    show("Round 2: version vectors + grow-only merge", vv_sync)


if __name__ == "__main__":
    main()
