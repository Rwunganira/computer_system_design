"""VaxRecords, first version. It works, and it leaks every child's record.

Read it like an attacker. Login checks a password and hands out a token, so it
*feels* secure, but /patients/<id> only asks "are you logged in?", never "may
YOU see THIS record?". A district officer who edits the ID in the URL reads
children in any district: an insecure direct object reference (IDOR).

Do not copy this file's patterns. secure_vax_api.py is the fixed version.
"""

import secrets

from flask import Flask, abort, jsonify, request

from course.data import population, vaccinations

# Synthetic users and synthetic passwords. Stored in plain text: another flaw.
USERS = {
    "amina": {"password": "amina-test-pw", "role": "district_officer", "district": "N-CEN"},
    "eric":  {"password": "eric-test-pw",  "role": "district_officer", "district": "S-COA"},
    "ruth":  {"password": "ruth-test-pw",  "role": "national"},
}


def load_patients(n=300):
    """{person_id: record} for a small synthetic population, with dose history."""
    people = population(n)
    doses = vaccinations(people)
    by_person = doses.groupby("person_id").vaccine.apply(list).to_dict()
    return {
        p.person_id: {
            "person_id": p.person_id,
            "name": f"{p.given_name} {p.family_name}",
            "birth_date": str(p.birth_date),
            "district_id": p.district_id,
            "doses": by_person.get(p.person_id, []),
        }
        for p in people.itertuples()
    }


PATIENTS = load_patients()


def logged_in_is_enough(user, patient):
    """The bug: being authenticated is treated as being authorized."""
    return True


def create_app(access_check=logged_in_is_enough):
    """Build the app. ``access_check(user, patient) -> bool`` decides record access."""
    app = Flask(__name__)
    tokens = {}  # token -> username

    @app.post("/login")
    def login():
        body = request.get_json(force=True)
        user = USERS.get(body.get("username"))
        if user is None or user["password"] != body.get("password"):
            abort(401)
        token = secrets.token_urlsafe(16)
        tokens[token] = body["username"]
        return jsonify(token=token)

    @app.get("/patients/<person_id>")
    def get_patient(person_id):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        username = tokens.get(token)
        if username is None:
            abort(401)
        patient = PATIENTS.get(person_id)
        if patient is None:
            abort(404)
        if not access_check(USERS[username], patient):
            abort(403)
        return jsonify(patient)

    return app
