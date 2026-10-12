"""Load a lesson's exercises (or its solutions) inside that lesson's tests.

Every lesson folder has an ``exercises.py`` for you to complete and a
``solutions.py`` with one worked answer. Tests call ``load_exercises(__file__)``
and get your ``exercises.py`` by default. Set ``COURSE_SOLUTIONS=1`` to run the
same tests against ``solutions.py`` instead:

    pytest lessons/01_complexity                     # checks your work
    COURSE_SOLUTIONS=1 pytest lessons/01_complexity  # checks the answers
"""

import importlib.util
import os
import sys
from pathlib import Path


def load_module(test_file, name):
    """Import ``<lesson folder>/<name>.py`` under a name unique to that lesson."""
    folder = Path(test_file).resolve().parent
    # Lesson files may import their sibling example modules by plain name.
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    unique = f"{folder.name}__{name}"
    if unique in sys.modules:
        return sys.modules[unique]
    spec = importlib.util.spec_from_file_location(unique, folder / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module


def load_exercises(test_file):
    """Return the lesson's exercises module, or its solutions if COURSE_SOLUTIONS is set."""
    use_solutions = os.environ.get("COURSE_SOLUTIONS", "") not in ("", "0")
    return load_module(test_file, "solutions" if use_solutions else "exercises")
