"""VaxRecords, secured: the guard model applied to every request.

  authenticate  salted, slow password hashes (hashlib.scrypt); bearer tokens
  authorize     role-based: a district officer reads only their own district
  audit         an append-only log of who asked for which record, and the answer
  services      SurveilLite calls VaxRecords with HMAC-signed requests

Run it to watch the IDOR attack succeed against vax_api_insecure.py and then
fail against this version.
"""

import hashlib
import hmac
import json
import logging
import secrets
import threading
import time

import requests
from flask import Flask, abort, g, jsonify, request
from werkzeug.serving import make_server

import vax_api_insecure
from vax_api_insecure import PATIENTS


# --- Authentication: store a salt and a slow hash, never the password --------

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)  # a fresh random salt per user
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return salt, digest


def check_password(password, salt, digest):
    return hmac.compare_digest(hash_password(password, salt)[1], digest)  # constant time


# Same synthetic users as the insecure version, but only salt + hash are kept.
USERS = {}
for _name, _u in vax_api_insecure.USERS.items():
    _salt, _digest = hash_password(_u["password"])
    USERS[_name] = {k: v for k, v in _u.items() if k != "password"} | {"salt": _salt, "hash": _digest}


# --- Authorization: fail-safe defaults, least privilege ----------------------

def can_read(user, patient):
    if user.get("role") == "national":
        return True
    if user.get("role") == "district_officer":
        return user.get("district") == patient["district_id"]
    return False  # unknown role: deny


# --- Audit: append-only ------------------------------------------------------

class AuditLog:
    def __init__(self):
        self._entries = []

    def append(self, **fields):
        self._entries.append({"time": time.time(), **fields})

    @property
    def entries(self):
        return tuple(dict(e) for e in self._entries)  # copies: readers cannot edit history


# --- Service-to-service: HMAC over method, path, timestamp and body ----------

def sign(key, method, path, timestamp, body):
    message = f"{method}\n{path}\n{timestamp}\n".encode() + body
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def create_app(service_key, max_skew=60):
    app = Flask(__name__)
    app.audit = AuditLog()
    tokens = {}

    @app.before_request
    def authenticate():  # complete mediation: runs before every route
        if request.path == "/login" or request.path.startswith("/internal/"):
            return
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if token not in tokens:
            abort(401)
        g.username = tokens[token]

    @app.post("/login")
    def login():
        body = request.get_json(force=True)
        user = USERS.get(body.get("username", ""))
        if user is None or not check_password(body.get("password", ""), user["salt"], user["hash"]):
            app.audit.append(user=body.get("username"), action="login", outcome="denied")
            abort(401)
        token = secrets.token_urlsafe(16)
        tokens[token] = body["username"]
        app.audit.append(user=body["username"], action="login", outcome="ok")
        return jsonify(token=token)

    @app.get("/patients/<person_id>")
    def get_patient(person_id):
        patient = PATIENTS.get(person_id)
        allowed = patient is not None and can_read(USERS[g.username], patient)
        app.audit.append(user=g.username, action="read", record=person_id,
                         outcome="ok" if allowed else "denied")
        if not allowed:
            abort(403)  # same answer for "missing" and "forbidden": no probing for IDs
        return jsonify(patient)

    @app.post("/internal/coverage")
    def coverage():
        ts = request.headers.get("X-Timestamp", "0")
        expected = sign(service_key, request.method, request.path, ts, request.get_data())
        fresh = ts.isdigit() and abs(time.time() - int(ts)) <= max_skew
        if not (fresh and hmac.compare_digest(expected, request.headers.get("X-Signature", ""))):
            app.audit.append(user="service?", action="coverage", outcome="bad signature")
            abort(401)
        district = request.get_json()["district"]
        kids = [p for p in PATIENTS.values() if p["district_id"] == district]
        pct = 100 * sum("MCV1" in p["doses"] for p in kids) / max(len(kids), 1)
        return jsonify(district=district, mcv1_coverage_pct=round(pct, 1))

    return app


# --- Demo ---------------------------------------------------------------------

def serve(app):
    server = make_server("127.0.0.1", 0, app)  # port 0: the OS picks a free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}", server


def attack(base, label):
    """Amina, a North-Central officer, edits the ID in the URL."""
    token = requests.post(f"{base}/login", json={"username": "amina",
                          "password": vax_api_insecure.USERS["amina"]["password"]}).json()["token"]
    auth = {"Authorization": f"Bearer {token}"}
    leaked, refused = {}, 0
    for i in range(1, 31):
        r = requests.get(f"{base}/patients/P{i:06d}", headers=auth)
        refused += r.status_code == 403
        if r.ok and r.json()["district_id"] != "N-CEN":
            leaked[r.json()["person_id"]] = r.json()["district_id"]
    print(f"[{label}] amina requests P000001..P000030: {len(leaked)} records leaked "
          f"from {len(set(leaked.values()))} other districts, {refused} refused")
    if leaked:
        pid = next(iter(leaked))
        print(f"   e.g. {pid}: {requests.get(f'{base}/patients/{pid}', headers=auth).json()}")


def main():
    logging.getLogger("werkzeug").setLevel(logging.ERROR)  # quiet the request log
    key = secrets.token_bytes(32)  # shared by VaxRecords and SurveilLite only
    insecure_url, s1 = serve(vax_api_insecure.create_app())
    secure_url, s2 = serve(app := create_app(key))

    attack(insecure_url, "insecure")
    attack(secure_url, "secure  ")
    print(f"[secure  ] no token: HTTP {requests.get(f'{secure_url}/patients/P000001').status_code}")

    entries = app.audit.entries
    print(f"\nAudit log: {len(entries)} entries, "
          f"{sum(e['outcome'] == 'denied' for e in entries)} denied. Last two:")
    for e in entries[-2:]:
        print("  ", {k: v for k, v in e.items() if k != "time"})

    print("\nSurveilLite -> VaxRecords, HMAC-signed:")
    url, path = f"{secure_url}/internal/coverage", "/internal/coverage"
    body, now = json.dumps({"district": "S-COA"}).encode(), str(int(time.time()))
    old = str(int(now) - 600)  # a genuine request captured 10 minutes ago
    altered = body.replace(b"S-COA", b"N-CEN")
    for label, b, t, sig in [("genuine request", body, now, sign(key, "POST", path, now, body)),
                             ("body altered in transit", altered, now, sign(key, "POST", path, now, body)),
                             ("replayed 10 minutes later", body, old, sign(key, "POST", path, old, body)),
                             ("signed with a guessed key", body, now, sign(b"guess", "POST", path, now, body))]:
        headers = {"Content-Type": "application/json", "X-Timestamp": t, "X-Signature": sig}
        r = requests.post(url, data=b, headers=headers)
        print(f"   {label:<26} HTTP {r.status_code} {r.json() if r.ok else ''}")
    s1.shutdown(), s2.shutdown()


if __name__ == "__main__":
    main()
