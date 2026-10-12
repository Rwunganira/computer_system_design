"""Module 2 worked answers."""

import case_definition as cd

# The exercises module defines RecordStore; reuse it rather than copying it.
from course.testing import load_module

RecordStore = load_module(__file__, "exercises").RecordStore


class NotParser(cd.Parser):
    def parse_atom(self):
        if self.peek() == ("keyword", "NOT"):
            self.take("keyword", "NOT")
            return ("not", self.parse_atom())
        return super().parse_atom()


class NotInterpreter(cd.RecordInterpreter):
    def eval_not(self, node, record):
        return not self.evaluate(node[1], record)


class WithinParser(cd.Parser):
    def parse_atom(self):
        atom = super().parse_atom()
        if self.peek() != ("keyword", "WITHIN"):
            return atom
        self.take("keyword", "WITHIN")
        days = self.take("num")
        self.take("keyword", "DAYS")
        self.take("keyword", "OF")
        return ("within", atom, days, self.take("name"))


class WithinInterpreter(cd.RecordInterpreter):
    def __init__(self):
        self.onset = {}

    def before_each(self, record):
        self.onset.setdefault(record["person_id"], record["date"])

    def eval_within(self, node, record):
        _, child, days, ref = node
        if ref != "onset":
            raise ValueError(f"unknown reference date {ref!r}")
        elapsed = (record["date"] - self.onset[record["person_id"]]).days
        return 0 <= elapsed <= days and self.evaluate(child, record)


def uncoordinated_updates(store, person_id, dose_a, dose_b):
    doses_a, _ = store.read(person_id)   # A reads
    doses_b, _ = store.read(person_id)   # B reads the same old value
    store.write(person_id, doses_a + [dose_a])  # A writes
    store.write(person_id, doses_b + [dose_b])  # B overwrites A: dose_a is lost
    return store.read(person_id)[0]


def coordinated_update(store, person_id, dose, max_tries=10):
    for _ in range(max_tries):
        doses, version = store.read(person_id)
        doses.append(dose)
        if store.write_if(person_id, doses, version):
            return doses
    raise RuntimeError(f"could not update {person_id} after {max_tries} tries")
