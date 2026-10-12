"""Run every lesson's example scripts and report any that fail.

    python scripts/run_examples.py
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"exercises.py", "solutions.py"}
# Long-running services you start by hand; their demos (e.g. rpc_demo.py) exercise them.
SERVICES = {"vax_server.py"}


def examples():
    for lesson in sorted((ROOT / "lessons").iterdir()):
        for script in sorted(lesson.glob("*.py")):
            if script.name in SKIP | SERVICES or script.name.startswith("test_"):
                continue
            # Only scripts meant to be run directly.
            if 'if __name__ == "__main__"' in script.read_text():
                yield script


def main():
    failed = []
    for script in examples():
        start = time.perf_counter()
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True, timeout=120)
        took = time.perf_counter() - start
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"{status:>6}  {took:5.1f}s  {script.relative_to(ROOT)}")
        if result.returncode != 0:
            failed.append(script)
            print(result.stderr[-2000:])
    if failed:
        sys.exit(f"{len(failed)} example(s) failed")


if __name__ == "__main__":
    main()
