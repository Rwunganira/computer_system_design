"""Duplicate doses from a retrying client, then the fix with idempotency keys.

Starts the VaxRecords service in a background thread on a free localhost port,
then records the same ten doses twice over a network that loses replies:
first with the naive retrying client, then with idempotency keys.

    python lessons/04_client_service/rpc_demo.py
"""

import logging
import threading
from collections import Counter

from werkzeug.serving import make_server

from course.data import population
from vax_client import VaxClient
from vax_server import DoseStore, create_app

DROP_RATE = 0.3  # three replies in ten are "lost" after the dose is saved
logging.getLogger("werkzeug").setLevel(logging.ERROR)  # hide the per-request log lines


def start_service(store):
    """Run VaxRecords in a background thread; return (base_url, server)."""
    app = create_app(store=store, drop_rate=DROP_RATE, seed=4, drop_delay=0.6)
    server = make_server("127.0.0.1", 0, app, threaded=True)  # port 0: pick any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}", server


def todays_doses(n=10):
    """Ten MCV1 doses for ten synthetic children at clinic C01."""
    kids = population(n)
    return [{"person_id": pid, "vaccine": "MCV1", "clinic_id": "C01", "dose_date": "2026-03-02"}
            for pid in kids.person_id]


def run(idempotent):
    store = DoseStore()
    base_url, server = start_service(store)
    client = VaxClient(base_url, idempotent=idempotent)
    try:
        for dose in todays_doses():
            client.record_dose(dose)
    finally:
        server.shutdown()

    per_child = Counter(d["person_id"] for d in store.doses)
    twice = sorted(f"{pid} x{n}" for pid, n in per_child.items() if n > 1)
    label = "with idempotency keys" if idempotent else "naive retrying client"
    print(f"--- {label} ---")
    print(f"doses given: 10   timeouts the client saw: {client.timeouts_seen}   "
          f"doses the service recorded: {len(store.doses)}")
    if twice:
        print(f"children recorded more than once: {', '.join(twice)}")
        print("  -> the register says they had extra MCV1 doses they never got.")
    else:
        print("every child recorded exactly once, despite the same lost replies.")
    print()
    return len(store.doses)


def main():
    print("A local call runs once or raises. A remote call may also go unanswered,")
    print(f"and here {DROP_RATE:.0%} of replies are lost *after* the dose is saved.\n")
    naive = run(idempotent=False)
    safe = run(idempotent=True)
    print(f"Retrying alone is at-least-once ({naive} records for 10 doses).")
    print(f"Retrying plus a key the service remembers is effectively exactly-once ({safe}).")


if __name__ == "__main__":
    main()
