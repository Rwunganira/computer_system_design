"""Module 2 exercises. Complete each TODO, then run: pytest lessons/02_elements

Exercises 1 and 2 extend the interpreter in case_definition.py by subclassing it, so the
example itself stays unchanged. Read its Parser and RecordInterpreter classes first.
"""

import case_definition as cd


# --- Exercise 1: a NOT operator --------------------------------------------------------
# The tokenizer already knows NOT is a keyword; the parser and the interpreter do not.
# NOT binds tighter than AND and OR, so "NOT fever AND rash" means "(NOT fever) AND rash".


class NotParser(cd.Parser):
    def parse_atom(self):
        """If the next token is the keyword NOT, consume it and return ("not", <atom>),
        where <atom> is parsed by calling parse_atom again (so "NOT NOT x" works).
        Otherwise, parse an ordinary atom with the parent class."""
        # TODO
        raise NotImplementedError


class NotInterpreter(cd.RecordInterpreter):
    def eval_not(self, node, record):
        """Execute a ("not", child) node: the opposite of the child's value."""
        # TODO
        raise NotImplementedError


# --- Exercise 2: WITHIN n DAYS OF onset, an operator with state -------------------------
# Records now have a "person_id" and a visit "date" (a datetime.date). A patient's onset is
# the date of the FIRST record for that person the interpreter has seen. The rule
#     rash WITHIN 14 DAYS OF onset
# is true for a record when rash is true AND the record's date is 0 to 14 days after that
# person's onset. The answer for one record depends on earlier records: the interpreter must
# remember something between records, as a processor keeps values in registers.


class WithinParser(cd.Parser):
    def parse_atom(self):
        """Parse an ordinary atom with the parent class. Then, if the next token is the keyword
        WITHIN, consume WITHIN <num> DAYS OF <name> and return
        ("within", <atom>, <num>, <name>). Otherwise return the atom unchanged."""
        # TODO: use self.peek() and self.take(kind, value) from cd.Parser.
        raise NotImplementedError


class WithinInterpreter(cd.RecordInterpreter):
    def __init__(self):
        self.onset = {}  # person_id -> date of the first record seen for that person

    def before_each(self, record):
        """Called by run() before each record: remember the person's onset if it is new."""
        # TODO
        raise NotImplementedError

    def eval_within(self, node, record):
        """Execute ("within", child, days, "onset")."""
        # TODO: raise ValueError if the reference name is anything but "onset".
        raise NotImplementedError


# --- Exercise 3: two clinics, one record, no coordination -------------------------------


class RecordStore:
    """A memory abstraction with READ and WRITE, plus a version number per name.

    read(name) returns (value, version). write(name, value) stores a value and bumps the
    version. write_if(name, value, expected_version) writes only if nobody has written since
    you read; it returns True if the write happened, False if it did not.
    """

    def __init__(self):
        self._cells = {}

    def read(self, name):
        value, version = self._cells.get(name, ([], 0))
        return list(value), version

    def write(self, name, value):
        _, version = self._cells.get(name, ([], 0))
        self._cells[name] = (list(value), version + 1)

    def write_if(self, name, value, expected_version):
        if self._cells.get(name, ([], 0))[1] != expected_version:
            return False
        self.write(name, value)
        return True


def uncoordinated_updates(store, person_id, dose_a, dose_b):
    """Clinic A adds dose_a and Clinic B adds dose_b to the list stored under person_id.

    Each clinic does read, append, write, with this interleaving:
        A reads, B reads, A writes, B writes.
    Use store.read and store.write only. Return the list stored at the end.
    (The test shows what this interleaving does to Clinic A's dose.)
    """
    # TODO
    raise NotImplementedError


def coordinated_update(store, person_id, dose, max_tries=10):
    """Add one dose to the list under person_id without losing anyone else's update.

    Read, append, then write_if with the version you read. If write_if returns False,
    someone wrote in between: read again and retry, up to max_tries times. Return the list
    you finally wrote. Raise RuntimeError if every try fails.
    """
    # TODO
    raise NotImplementedError
