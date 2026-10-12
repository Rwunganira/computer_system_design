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


def split_key_ideas(folder):
    """Return (overview, check_yourself) from key_ideas.md, or ("", "") if absent."""
    path = folder / "key_ideas.md"
    if not path.exists():
        return "", ""
    text = path.read_text()
    overview, _, check = text.partition("## Check yourself")
    overview = overview.replace("## In one minute", '<div class="one-minute" markdown>\n\n## In one minute', 1)
    overview = overview.replace("## The picture", "</div>\n\n## The picture", 1)
    if check:
        # Style the questions as question callouts; <summary> is HTML, so render `code` by hand.
        check = check.replace('<details markdown="1">', '<details class="question" markdown="1">')
        check = re.sub(r"<summary>(.*?)</summary>",
                       lambda m: "<summary>" + re.sub(r"`([^`]+)`", r"<code>\1</code>", m.group(1)) + "</summary>",
                       check)
    return overview.strip(), ("## Check yourself" + check).strip() if check else ""


def insert_after_intro(readme, block):
    """Put ``block`` after the title and opening callouts, before the README's first section."""
    match = re.search(r"^## ", readme, flags=re.M)
    if not match or not block:
        return readme + "\n\n" + block
    return readme[:match.start()] + block + "\n\n" + readme[match.start():]


def module_page(folder):
    readme = style_readme((folder / "README.md").read_text()).rstrip()
    overview, check = split_key_ideas(folder)
    parts = [insert_after_intro(readme, overview), ""]
    if check:
        parts += [check, ""]
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
[Glossary](glossary.md){{ .md-button }}

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

1. **Skim** the module's *In one minute* summary and *The picture* diagram.
2. **Read** the chapter alongside the rest of the module page.
3. **Predict** what the examples will do, then **run** them and see if you were right.
4. **Answer** the *Check yourself* questions before opening the answers.
5. **Complete** the exercises in `exercises.py` until `pytest` passes, then compare with the worked solution.

```bash
git clone {REPO}
cd computer_system_design
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
pytest lessons/00_setup
```
"""


# Everyday words that would put a tooltip on half the course; they stay on the glossary page.
NO_TOOLTIP = {"Context", "Error", "Failure", "Fault", "Lock", "Thread", "Binding", "Interpreter",
              "Hierarchy", "Abstraction", "Caching", "Batching", "Acknowledgement", "Retransmission",
              "Layering", "Modularity", "Authentication", "Authorization", "Availability", "Checksum"}


def glossary_terms():
    text = (ROOT / "GLOSSARY.md").read_text()
    return re.findall(r"^- \*\*(.+?)\*\*: (.+)$", text, flags=re.M)


def tooltip_definitions():
    """Abbreviation lines that make every glossary term show its definition on hover."""
    lines = []
    for term, definition in glossary_terms():
        if term in NO_TOOLTIP:
            continue
        definition = definition.replace('"', "'")
        for variant in {term, term[0].lower() + term[1:]}:
            lines.append(f"*[{variant}]: {definition}")
    return "\n".join(lines) + "\n"


def build_sources():
    if SRC.exists():
        shutil.rmtree(SRC)
    (SRC / "lessons").mkdir(parents=True)
    (SRC / "index.md").write_text(home_page())
    outline = (ROOT / "COURSE_OUTLINE.md").read_text()
    (SRC / "outline.md").write_text(outline)
    for folder in lessons():
        (SRC / "lessons" / f"{folder.name}.md").write_text(module_page(folder))
    (SRC / "glossary.md").write_text((ROOT / "GLOSSARY.md").read_text())
    (SRC / "assets").mkdir()
    shutil.copytree(ROOT / "docs_theme", SRC / "assets", dirs_exist_ok=True)
    (ROOT / "site_includes").mkdir(exist_ok=True)
    (ROOT / "site_includes" / "glossary_tooltips.md").write_text(tooltip_definitions())


if __name__ == "__main__":
    build_sources()
    command = "serve" if "--serve" in sys.argv else "build"
    args = [sys.executable, "-m", "mkdocs", command, "-f", str(ROOT / "mkdocs.yml")]
    if command == "build":
        args.append("--strict")
    subprocess.run(args, cwd=ROOT, check=True)
