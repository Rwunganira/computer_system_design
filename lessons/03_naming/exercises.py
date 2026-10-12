"""Module 3 exercises. Complete each TODO, then run: pytest lessons/03_naming"""

import pandas as pd
from flask import Flask, jsonify

from course.data import DISTRICTS


class AmbiguousName(LookupError):
    """A name bound to more than one value in the context where it was looked up."""

    def __init__(self, name, candidates):
        super().__init__(f"{name!r} is ambiguous: {candidates}")
        self.name = name
        self.candidates = candidates  # sorted list of district_ids


# --- Exercise 1: two districts called "Central" ----------------------------------------
# patient_resolver.create_app built {district_name: district_id}, so "Central" silently meant
# South Central and North Central had no URL at all. Fix the naming without breaking the
# URLs that worked: /districts/Riverside/cases must keep returning the same thing.


def resolve_district(name, region=None, districts=DISTRICTS):
    """Return the district_id that ``name`` refers to.

    - A district_id ("N-CEN") is already unambiguous: return it as it is.
    - Otherwise match ``name`` against district_name, only within ``region`` if one is given.
    - No match: raise LookupError. More than one match: raise AmbiguousName with the
      sorted candidate district_ids.
    """
    # TODO
    raise NotImplementedError


def create_district_app(reports, districts=DISTRICTS):
    """A Flask app serving total cases per district under two kinds of URL:

        GET /districts/<name>/cases                         name or district_id
        GET /regions/<region>/districts/<name>/cases        name qualified by region

    Success: 200 and JSON {"district_id": ..., "cases": <total cases, int>}.
    Unknown name: 404 and JSON {"error": ...}.
    Ambiguous name: 300 (Multiple Choices) and JSON {"candidates": [...]}, a sorted list of
    unambiguous URLs, e.g. "/districts/N-CEN/cases". Never guess.
    """
    # TODO: use resolve_district; sum reports.cases by district_id.
    raise NotImplementedError


# --- Exercise 2: renaming a clinic with an alias layer ---------------------------------
# Old reports name clinics by the name they had at the time. When a clinic is renamed, its
# old name becomes an alias: a name bound to another name, not to the clinic itself.


def resolve_clinic(name, clinic_ids, aliases, max_hops=10):
    """Return the clinic_id for ``name``.

    ``clinic_ids`` binds current clinic names to clinic_ids. ``aliases`` binds old names to
    newer names (which may themselves be old names, after several renames). Follow aliases
    until you reach a current name. Raise LookupError for a name bound in neither context,
    and also when following aliases takes more than ``max_hops`` steps (an alias loop).
    """
    # TODO
    raise NotImplementedError


def rename_clinic(clinic_ids, aliases, old, new):
    """Rename clinic ``old`` to ``new`` in place: rebind the clinic_id under the new name,
    remove the old binding, and add the alias old -> new. Raise LookupError if ``old`` is not
    a current name, and ValueError if ``new`` is already in use (current name or alias)."""
    # TODO
    raise NotImplementedError


# --- Exercise 3: one registry ID, two birth dates ---------------------------------------


def conflicting_birth_dates(records: pd.DataFrame) -> list:
    """``records`` has columns registry_id, birth_date and clinic: what each clinic recorded
    about the child it believes has that registry ID. Return the sorted list of registry_ids
    bound to records with more than one distinct birth_date. Such an ID may have merged two
    children, as the overloaded name in patient_resolver.py did."""
    # TODO
    raise NotImplementedError
