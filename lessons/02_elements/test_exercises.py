from datetime import date

import pytest

from course.testing import load_exercises, load_module

ex = load_exercises(__file__)
cd = load_module(__file__, "case_definition")


def matches(parser_cls, interpreter, rule, record):
    return interpreter.evaluate(parser_cls(rule).parse(), record)


# --- Exercise 1: NOT -------------------------------------------------------------------

def test_not_parses_to_a_not_node():
    assert ex.NotParser("NOT fever").parse() == ("not", ("var", "fever"))


def test_not_binds_tighter_than_and():
    assert ex.NotParser("NOT fever AND rash").parse() == ("and", ("not", ("var", "fever")), ("var", "rash"))


@pytest.mark.parametrize("rule, record, expected", [
    ("NOT fever", {"fever": False}, True),
    ("NOT fever", {"fever": True}, False),
    ("NOT NOT fever", {"fever": True}, True),
    ("cough AND NOT (fever OR rash)", {"cough": True, "fever": False, "rash": False}, True),
    ("cough AND NOT (fever OR rash)", {"cough": True, "fever": False, "rash": True}, False),
    ("NOT age < 5", {"age": 3}, False),
])
def test_not_evaluates(rule, record, expected):
    assert matches(ex.NotParser, ex.NotInterpreter(), rule, record) is expected


def test_old_rules_still_work():
    record = {"fever": True, "rash": False, "cough": True, "age": 4}
    rule = "fever AND (rash OR cough) AND age < 15"
    assert matches(ex.NotParser, ex.NotInterpreter(), rule, record) is True


# --- Exercise 2: WITHIN n DAYS OF onset ---------------------------------------------------

def test_within_parses():
    tree = ex.WithinParser("fever AND rash WITHIN 14 DAYS OF onset").parse()
    assert tree == ("and", ("var", "fever"), ("within", ("var", "rash"), 14, "onset"))


def test_within_remembers_onset_per_person():
    visits = [
        {"person_id": "A", "date": date(2026, 3, 1), "rash": False},   # A's onset
        {"person_id": "B", "date": date(2026, 3, 10), "rash": True},   # B's onset, day 0
        {"person_id": "A", "date": date(2026, 3, 15), "rash": True},   # A, day 14: counts
        {"person_id": "A", "date": date(2026, 3, 16), "rash": True},   # A, day 15: too late
        {"person_id": "B", "date": date(2026, 3, 20), "rash": True},   # B, day 10
        {"person_id": "B", "date": date(2026, 3, 21), "rash": False},  # no rash
    ]
    tree = ex.WithinParser("rash WITHIN 14 DAYS OF onset").parse()
    interp = ex.WithinInterpreter()
    assert interp.run(tree, visits) == [False, True, True, False, True, False]
    assert interp.onset == {"A": date(2026, 3, 1), "B": date(2026, 3, 10)}


def test_fresh_interpreter_has_fresh_state():
    tree = ex.WithinParser("rash WITHIN 7 DAYS OF onset").parse()
    late = [{"person_id": "A", "date": date(2026, 5, 1), "rash": True}]
    early = [{"person_id": "A", "date": date(2026, 1, 1), "rash": False}]
    interp = ex.WithinInterpreter()
    interp.run(tree, early)
    assert interp.run(tree, late) == [False]               # onset is still 1 January
    assert ex.WithinInterpreter().run(tree, late) == [True]  # a new interpreter starts over


def test_within_rejects_unknown_reference():
    tree = ex.WithinParser("rash WITHIN 7 DAYS OF discharge").parse()
    with pytest.raises(ValueError):
        ex.WithinInterpreter().run(tree, [{"person_id": "A", "date": date(2026, 1, 1), "rash": True}])


# --- Exercise 3: lost updates ------------------------------------------------------------

def test_uncoordinated_writes_lose_an_update():
    store = ex.RecordStore()
    store.write("P000001", ["BCG"])
    final = ex.uncoordinated_updates(store, "P000001", "OPV1@clinic_a", "DTP1@clinic_b")
    # Two doses were given, but the record shows only one of them: the last write won,
    # and Clinic A's dose is silently gone.
    assert final == ["BCG", "DTP1@clinic_b"]
    assert "OPV1@clinic_a" not in final


class RacyStore(ex.RecordStore):
    """The first conditional write finds that another clinic wrote in between."""

    def __init__(self):
        super().__init__()
        self.raced = False

    def write_if(self, name, value, expected_version):
        if not self.raced:
            self.raced = True
            doses, _ = self.read(name)
            self.write(name, doses + ["DTP1@clinic_b"])  # Clinic B sneaks in
        return super().write_if(name, value, expected_version)


def test_coordinated_update_keeps_both_doses():
    store = RacyStore()
    store.write("P000001", ["BCG"])
    final = ex.coordinated_update(store, "P000001", "OPV1@clinic_a")
    assert sorted(final) == ["BCG", "DTP1@clinic_b", "OPV1@clinic_a"]
    assert store.read("P000001")[0] == final


def test_coordinated_update_gives_up():
    class AlwaysBusy(ex.RecordStore):
        def write_if(self, name, value, expected_version):
            return False

    with pytest.raises(RuntimeError) as info:
        ex.coordinated_update(AlwaysBusy(), "P000001", "BCG", max_tries=3)
    assert not isinstance(info.value, NotImplementedError)  # a subclass of RuntimeError


def test_example_interpreters_agree():
    df = cd.line_list(n=500)
    tree = cd.parse("fever AND (rash OR cough) AND age < 15")
    assert list(cd.FrameInterpreter().evaluate(tree, df)) == cd.RecordInterpreter().run(tree, df.to_dict("records"))
