"""Assemble the course website's pages from the lessons, then build it with MkDocs.

The lessons stay the single source of truth: each module page is made from the
lesson's README.md, predict.md, example scripts, exercises.py and solutions.py.

    pip install -r requirements-site.txt
    python scripts/build_site.py          # writes site_src/, then builds site/
    python scripts/build_site.py --serve  # live preview at http://127.0.0.1:8000
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site_src"
REPO = "https://github.com/Rwunganira/computer_system_design"

# One short line per module for the home page cards: (icon, teaser).
CARDS = {
    "00_setup": (":material-rocket-launch:", "Install, meet SurveilLite and VaxRecords, and find the hidden cholera outbreak."),
    "01_complexity": (":material-graph-outline:", "Refactor a tangled dashboard and watch an O(n²) check fail to scale."),
    "02_elements": (":material-cpu-64-bit:", "Build an interpreter for case-definition rules."),
    "03_naming": (":material-card-account-details-outline:", "Resolve patient identifiers across clinics without merging two children."),
    "04_client_service": (":material-swap-horizontal:", "Split VaxRecords into a service and make retries safe."),
    "05_virtualization": (":material-layers-triple-outline:", "A threaded lab-result pipeline with a bounded buffer."),
    "06_performance": (":material-speedometer:", "Profile the dashboard, then batch, cache and overlap."),
    "07_networks": (":material-cellphone-message:", "Reliable SMS case reporting over a lossy channel."),
    "08_fault_tolerance": (":material-shield-refresh-outline:", "Checksums, triple modular redundancy and availability."),
    "09_atomicity": (":material-atom-variant:", "Crash-safe dose recording with shadow copies, logs and two-phase commit."),
    "10_consistency": (":material-sync:", "Offline clinic tablets that sync without losing a dose."),
    "11_security": (":material-lock-outline:", "Authentication, authorization and a tamper-evident audit log."),
    "12_capstone": (":material-flag-checkered:", "A surveillance service that survives a scripted bad week."),
}


def lessons():
    return sorted(p for p in (ROOT / "lessons").iterdir() if (p / "README.md").exists())


def title_of(markdown):
    return markdown.splitlines()[0].lstrip("# ").strip()


def code_block(path, title=None):
    text = path.read_text().rstrip()
    return f'```python title="{title or path.name}"\n{text}\n```'


def indent(text, spaces=4):
    return "\n".join((" " * spaces + line) if line.strip() else "" for line in text.splitlines())


def style_readme(text):
    """Turn the README's "**Read in the book:**" and "**Goal:**" paragraphs into callouts."""
    lines = text.splitlines()
    out, i = [], 0
    while i < len(lines):
        m = re.match(r"\*\*(Read in the book|Goal):\*\*\s*(.*)", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        kind = "abstract" if m.group(1).startswith("Read") else "tip"
        first = m.group(2)
        para = [first[:1].upper() + first[1:]]
        i += 1
        while i < len(lines) and lines[i].strip():  # the rest of the paragraph
            para.append(lines[i])
            i += 1
        out += [f'!!! {kind} "{m.group(1)}"', ""] + ["    " + p for p in para]
    return "\n".join(out)


def module_page(folder):
    readme = (folder / "README.md").read_text()
    parts = [style_readme(readme).rstrip(), ""]
    source = f"{REPO}/tree/main/lessons/{folder.name}"
    parts.append(f'[:material-github: View this module on GitHub]({source}){{ .md-button }}\n')

    predict = folder / "predict.md"
    if predict.exists():
        body = "\n".join(predict.read_text().splitlines()[1:]).strip()
        parts += ["## Predict, then run", "",
                  '!!! question "Answer these before you run the examples"', "", indent(body), ""]

    examples = [p for p in sorted(folder.glob("*.py"))
                if p.name not in ("exercises.py", "solutions.py") and not p.name.startswith("test_")]
    if examples:
        parts += ["## Example code", ""]
        for p in examples:
            parts += [f'??? example "{p.name}"', "", indent(code_block(p)), ""]

    parts += ["## Your exercises", "",
              f"Open `lessons/{folder.name}/exercises.py`, complete each `TODO`, then check your work:", "",
              f"```bash\npytest lessons/{folder.name}\n```", "",
              indent(code_block(folder / "exercises.py"), 0), "",
              '??? success "Show the worked solution (try the exercises first)"', "",
              indent(code_block(folder / "solutions.py")), ""]
    return "\n".join(parts)


def home_page():
    cards = []
    for folder in lessons():
        title = title_of((folder / "README.md").read_text())
        label, _, name = title.partition(". ")
        icon, teaser = CARDS.get(folder.name, (":material-book-open-variant:", ""))
        cards.append(f"-   {icon}{{ .lg .middle }} __[{label}. {name}](lessons/{folder.name}.md)__\n\n    ---\n\n    {teaser}\n")
    return f"""---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# Computer System Design, in Python

<p class="hero-lead">A hands-on companion to Saltzer and Kaashoek's <em>Principles of Computer System Design</em>.
Each chapter's ideas become a small, runnable Python or Flask program from public health work,
with exercises you check yourself.</p>

[Start the course](lessons/00_setup.md){{ .md-button .md-button--primary }}
[Read the outline](outline.md){{ .md-button }}

</div>

## The running case

Every module works on the same two fictional systems, so each new idea lands on code you already know.

<div class="grid cards" markdown>

-   :material-chart-bell-curve-cumulative:{{ .lg .middle }} __SurveilLite__

    ---

    A disease surveillance dashboard. Forty clinics in eight districts report weekly measles,
    cholera and malaria counts; the dashboard computes incidence per 100,000 and flags outbreaks.

-   :material-needle:{{ .lg .middle }} __VaxRecords__

    ---

    A vaccination records API. Health workers record each dose given; the API keeps every child's
    history and every clinic's vaccine stock.

</div>

All data is synthetic, generated from a fixed seed. No real patients, clinics or places.

## Modules

<div class="grid cards" markdown>

{chr(10).join(cards)}
</div>

## How each module works

1. **Read** the chapter alongside the module page, which explains its ideas in plain language.
2. **Predict** what the examples will do, then **run** them and see if you were right.
3. **Complete** the exercises in `exercises.py` until `pytest` passes.
4. **Compare** with the worked solution.

```bash
git clone {REPO}
cd computer_system_design
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
pytest lessons/00_setup
```
"""


def build_sources():
    if SRC.exists():
        shutil.rmtree(SRC)
    (SRC / "lessons").mkdir(parents=True)
    (SRC / "index.md").write_text(home_page())
    outline = (ROOT / "COURSE_OUTLINE.md").read_text()
    (SRC / "outline.md").write_text(outline)
    for folder in lessons():
        (SRC / "lessons" / f"{folder.name}.md").write_text(module_page(folder))
    shutil.copytree(ROOT / "docs_theme", SRC / "assets")


if __name__ == "__main__":
    build_sources()
    command = "serve" if "--serve" in sys.argv else "build"
    args = [sys.executable, "-m", "mkdocs", command, "-f", str(ROOT / "mkdocs.yml")]
    if command == "build":
        args.append("--strict")
    subprocess.run(args, cwd=ROOT, check=True)
