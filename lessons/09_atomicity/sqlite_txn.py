"""Fix 3: let the database do it. Two writes inside one SQLite transaction.

SQLite keeps its own journal (a rollback journal or a write-ahead log) and runs
recovery whenever it opens the database file. Everything between BEGIN and
COMMIT is all-or-nothing, and the same lock that protects the transaction also
gives before-or-after atomicity between concurrent writers.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

from dose_recorder_naive import INITIAL_STOCK, initial_stock, sample_doses

SCHEMA = """
CREATE TABLE history (dose_id INTEGER PRIMARY KEY, person_id TEXT, vaccine TEXT, clinic_id TEXT);
CREATE TABLE stock (clinic_id TEXT, vaccine TEXT, doses_left INTEGER CHECK (doses_left >= 0),
                    PRIMARY KEY (clinic_id, vaccine));
"""


def setup(path):
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO stock VALUES (?, ?, ?)",
                         [(c, v, n) for c, vs in initial_stock().items() for v, n in vs.items()])
    conn.close()


def connect(path):
    # isolation_level=None: we write BEGIN and COMMIT ourselves, so nothing is hidden.
    return sqlite3.connect(path, isolation_level=None)


def record_dose(conn, dose, hook=None, use_transaction=True):
    hook = hook or (lambda i: None)
    if use_transaction:
        conn.execute("BEGIN IMMEDIATE")      # take the write lock now
    try:
        hook(0)
        conn.execute("INSERT INTO history VALUES (:dose_id, :person_id, :vaccine, :clinic_id)", dose)
        hook(1)
        conn.execute("UPDATE stock SET doses_left = doses_left - 1 WHERE clinic_id = ? AND vaccine = ?",
                     (dose["clinic_id"], dose["vaccine"]))
        hook(2)
        if use_transaction:
            conn.execute("COMMIT")           # the commit point
    except BaseException:
        if use_transaction:
            conn.execute("ROLLBACK")         # also what SQLite's recovery does after a real crash
        raise


def is_consistent(conn):
    bad = conn.execute("""
        SELECT COUNT(*) FROM stock s
        LEFT JOIN (SELECT clinic_id, vaccine, COUNT(*) AS n FROM history GROUP BY 1, 2) h
               ON h.clinic_id = s.clinic_id AND h.vaccine = s.vaccine
        WHERE s.doses_left + COALESCE(h.n, 0) != ?""", (INITIAL_STOCK,)).fetchone()[0]
    return bad == 0


def describe(path, dose):
    conn = connect(path)                     # a fresh connection, as after a restart
    given = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
    left = conn.execute("SELECT doses_left FROM stock WHERE clinic_id = ? AND vaccine = ?",
                        (dose["clinic_id"], dose["vaccine"])).fetchone()[0]
    ok = "consistent" if is_consistent(conn) else "INCONSISTENT"
    conn.close()
    return f"{given} doses, stock {left} -> {ok}"


def crashing_child(path, use_transaction):
    """Runs in a separate process that dies between the two writes. os._exit skips
    every except, finally and ROLLBACK: as close to pulling the plug as Python gets."""
    conn = connect(path)
    record_dose(conn, sample_doses(2)[1], use_transaction=use_transaction,
                hook=lambda i: os._exit(1) if i == 1 else None)


def main():
    first, second = sample_doses(2)
    with tempfile.TemporaryDirectory() as tmp:
        for use_transaction in (False, True):
            path = Path(tmp) / f"vax_{use_transaction}.db"
            setup(path)
            conn = connect(path)
            record_dose(conn, first, use_transaction=use_transaction)
            conn.close()
            child = subprocess.run([sys.executable, __file__, "--crash-child", str(path), str(use_transaction)])
            label = "inside BEGIN ... COMMIT" if use_transaction else "autocommit, no transaction"
            print(f"Process killed between the two writes (exit code {child.returncode}), {label}:")
            print(f"   reopened: {describe(path, second)}\n")

        print("A database constraint is a fail-fast check that also rolls back. Empty the stock:")
        path = Path(tmp) / "vax_True.db"
        conn = connect(path)
        conn.execute("UPDATE stock SET doses_left = 0 WHERE clinic_id = ? AND vaccine = ?",
                     (second["clinic_id"], second["vaccine"]))
        try:
            record_dose(conn, second)
        except sqlite3.IntegrityError as e:
            print(f"   IntegrityError: {e}; the history insert was rolled back too")
        rows = conn.execute("SELECT COUNT(*) FROM history WHERE dose_id = ?", (second["dose_id"],)).fetchone()[0]
        print(f"   dose {second['dose_id']} rows in history: {rows}")
        conn.close()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--crash-child"]:
        crashing_child(sys.argv[2], sys.argv[3] == "True")
    else:
        main()
