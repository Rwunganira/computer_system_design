"""Two-phase commit between VaxRecords and a separate stock service (in-process).

Now history and stock belong to two different services, each with its own
storage. Neither can see the other's files, so no single os.replace or SQLite
transaction covers both. A coordinator runs two-phase commit:

  Phase 1 (prepare): ask each participant "can you do your part?" A participant
          that votes yes must be able to commit later even if it crashes, so it
          records its tentative change durably and enters the PREPARED state.
  Commit point:     the coordinator writes its decision to its own log.
  Phase 2:          tell every participant the decision; each commits or aborts.
"""

from dose_recorder_naive import Crash, add_dose, initial_stock, sample_doses


class Participant:
    """Keeps tentative changes apart from committed state, keyed by transaction id.

    Here ``status`` and ``pending`` live in memory to keep the example short. A real
    participant writes them to its own log (as in wal_recorder.py) before voting
    yes, so that a prepared transaction survives the participant crashing."""

    def __init__(self, name):
        self.name = name
        self.status = {}      # tid -> "prepared" | "committed" | "aborted"
        self.pending = {}     # tid -> the dose, held until the decision arrives

    def prepare(self, tid, dose):
        if not self.can_do(dose):
            self.status[tid] = "aborted"
            return "no"
        self.pending[tid] = dose
        self.status[tid] = "prepared"   # from here on, this participant may not abort alone
        return "yes"

    def commit(self, tid):
        if self.status.get(tid) == "prepared":
            self.apply(self.pending.pop(tid))
            self.status[tid] = "committed"

    def abort(self, tid):
        self.pending.pop(tid, None)
        self.status[tid] = "aborted"


class VaxRecordsService(Participant):
    def __init__(self):
        super().__init__("VaxRecords")
        self.history = {}

    def can_do(self, dose):
        return True

    def apply(self, dose):
        add_dose(self.history, dose)


class StockService(Participant):
    def __init__(self):
        super().__init__("Stock")
        self.stock = initial_stock()

    def can_do(self, dose):
        reserved = sum(1 for d in self.pending.values()
                       if (d["clinic_id"], d["vaccine"]) == (dose["clinic_id"], dose["vaccine"]))
        return self.stock[dose["clinic_id"]][dose["vaccine"]] - reserved > 0

    def apply(self, dose):
        self.stock[dose["clinic_id"]][dose["vaccine"]] -= 1


class Coordinator:
    def __init__(self, participants):
        self.participants = participants
        self.log = []                     # durable decisions: (tid, "commit" | "abort")

    def run(self, tid, dose, crash_after_decision=False):
        votes = {p.name: p.prepare(tid, dose) for p in self.participants}
        decision = "commit" if all(v == "yes" for v in votes.values()) else "abort"
        self.log.append((tid, decision))  # the commit point
        if crash_after_decision:
            raise Crash("coordinator crashed after logging its decision")
        self.send(tid, decision)
        return votes, decision

    def send(self, tid, decision):
        for p in self.participants:
            p.commit(tid) if decision == "commit" else p.abort(tid)

    def recover(self):
        """On restart: resend every logged decision. Commit and abort are idempotent."""
        for tid, decision in self.log:
            self.send(tid, decision)


def show(vax, stock, dose, tid):
    left = stock.stock[dose["clinic_id"]][dose["vaccine"]]
    doses = sum(len(v) for v in vax.history.values())
    print(f"   VaxRecords: {doses} doses ({vax.status.get(tid)}),  "
          f"Stock: {dose['clinic_id']} {dose['vaccine']} = {left} ({stock.status.get(tid)})")


def main():
    vax, stock = VaxRecordsService(), StockService()
    coord = Coordinator([vax, stock])
    d1, d2, d3 = sample_doses(3)

    print("1. A normal dose:")
    votes, decision = coord.run("t1", d1)
    print(f"   votes {votes} -> {decision}")
    show(vax, stock, d1, "t1")

    print("\n2. The clinic has run out of that vaccine, so the stock service votes no:")
    stock.stock[d2["clinic_id"]][d2["vaccine"]] = 0
    votes, decision = coord.run("t2", d2)
    print(f"   votes {votes} -> {decision}")
    show(vax, stock, d2, "t2")
    print("   VaxRecords voted yes, but the dose is not in the history: all or nothing.")

    print("\n3. The coordinator crashes after deciding, before telling anyone:")
    try:
        coord.run("t3", d3, crash_after_decision=True)
    except Crash as e:
        print(f"   {e}")
    show(vax, stock, d3, "t3")
    print("   Both participants are PREPARED and in doubt: they voted yes, so they may not")
    print("   abort on their own, and they do not know the decision. They are blocked.")
    coord.recover()
    print("   Coordinator restarts and resends its logged decision:")
    show(vax, stock, d3, "t3")


if __name__ == "__main__":
    main()
