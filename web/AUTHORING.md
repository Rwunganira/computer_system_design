# Authoring a module

The website is a set of static HTML pages in this `web/` folder that share `course.css` and `course.js`.
The engine and design come from the author's earlier course, *Introduction to Computational Thinking and
Data Science*; its finished reference lesson is
`/home/claude/rwunganira/intro_computation_data_science/l01.html` (and l02 to l20 beside it).
**Read that l01 fully before writing**, and match its voice, density, structure and polish. Module pages are
`m00.html` to `m12.html` here, with `<body data-lesson="m05">` etc.

## Audience and goal
A working Python developer (Flask, pandas) with a master's in epidemiology who has read Guttag's
*Introduction to Computation and Programming Using Python* and is reading Saltzer and Kaashoek,
*Principles of Computer System Design: An Introduction* (2009). Each module pairs one chapter's ideas with
runnable examples anchored in two fictional health systems: **SurveilLite** (a disease surveillance dashboard:
40 clinics in 8 districts report weekly measles, cholera and malaria counts) and **VaxRecords** (a vaccination
records API: doses given, each child's history, each clinic's stock). All data is synthetic.

The content of each module already exists in the repository and is the source of truth: read
`../lessons/NN_topic/README.md`, `key_ideas.md` (summary, diagram, self-check questions), `predict.md`,
the example scripts, `exercises.py`, `solutions.py` and `../GLOSSARY.md`. The web page teaches the same ideas
with the same names and numbers, but as an interactive lesson. Use the book's vocabulary accurately; do not
invent section numbers or quotes from the book. Do not claim to be affiliated with the authors or MIT.

The repository's local labs use Flask, threads, SQLite, hashlib and pandas, which cannot run in the browser.
On the web page, teach the same mechanism with plain Python that runs in Skulpt (see "Python runtime"), and
end the page's last content section with a short box pointing to the full lab:
`<div class="callout"><b>Run the full lab.</b> ... <code>pytest lessons/NN_topic</code> ... <a href="https://github.com/Rwunganira/computer_system_design/tree/main/lessons/NN_topic">lessons/NN_topic on GitHub</a></div>`
(check course.css for the exact callout class names that l01 uses and use those).

## Learning design (required in every module)
- Hero: an eyebrow `Computer System Design · Module N`, an `h1` that states the big idea in one sentence with
  one or two `<em>` words, a lede, and **one live interactive visual that shows the module's core mechanism**
  (for example: an SMS channel dropping and duplicating packets, two threads interleaving a read-modify-write,
  a crash slider over the steps of a write-ahead log). Hand-built SVG/Canvas/DOM, in the page's own inline
  script. Then a 3-box `.organizer` (You will learn / You will build / How it works).
- 6 to 9 `section.lesson` blocks with ids `s1`…`sN`, each `.sec-head` with `.sec-num` and `h2`.
  Optional `data-short="Short name"` for the rail.
- Per concept: explanation, then a **worked example** (tag `worked`, ideally a step-through widget), then a
  **predict-then-run** cell (`data-predict="<exact last line of output>"` + `.predict` input), then a
  **You try** exercise (tag `try`, self-checking), then a **Quick check** quiz (`.quiz[data-quiz="sN"]`).
- At least 2 self-checking exercises per module, one a *faded example* (partly written code to complete).
  Base them on the module's `exercises.py` where the idea fits the browser.
- At least 2 step-through or interactive widgets beyond plain code cells.
- Last section: "Recall and review" with `.deck-host` flashcards (8 to 12 cards, drawn from the module's
  glossary terms and key ideas), a mixed interleaved quiz (3 questions spanning all sections), `#schedule`
  spaced-review dates (`<div class="schedule" id="schedule"></div>`), and a `.next` box previewing the next
  module (see l01). The engine adds prev/next module links itself.
- Every section that has a `.quiz[data-quiz]` must have quiz data with that key; each quiz item has
  `q` (HTML), optional `code`, `o` (options, HTML), `a` (index of correct), `why` (explanation shown when correct).
  Make distractors reflect real misconceptions.
- Footer: like l01's, but the sources line reads: Follows Saltzer and Kaashoek, *Principles of Computer System
  Design: An Introduction* (2009), Chapter N; links to the course repository
  https://github.com/Rwunganira/computer_system_design ; "Not affiliated with the authors or MIT. All data is synthetic."

## Engine API (course.js)
- Code cell markup (exactly):
  ```html
  <div class="cell" data-predict="25">            <!-- data-predict optional; data-limit="20000" ms optional -->
    <div class="predict"><label for="p-x">Predict the last line:</label><input id="p-x" autocomplete="off" placeholder="your guess"></div>
    <div class="ed"><pre class="hl"></pre><textarea class="src" id="code-UNIQUE" spellcheck="false" aria-label="Python code">...python...</textarea></div>
  </div>
  ```
  The engine adds the Run/Reset bar. Every textarea needs a page-unique id. Escape `<`, `>` and `&` inside textareas
  as `&lt;` `&gt;` `&amp;` to be safe.
- Exercise: a cell with `id="ex-NAME"` (no predict) plus an entry in `exercises` passed to `CT.lesson`:
  ```js
  "ex-NAME": { cases: [...], solution: "python source", hint: ["first hint", "stronger hint"], limit: 8000 }
  ```
  A case is either a **string of Python appended after the learner's code** (output after it is compared; e.g.
  `"print(fib(10))"`), or an **object of variable values** substituted into `name = ...` lines (whole output compared).
  Expected output = running `solution` on the same case, so the solution must be correct. Give 4–6 cases including
  edge cases. The starter code must NOT already pass. "Show solution" unlocks after 2 failed checks.
- `CT.lesson({ quiz: {s1: [...], ...}, cards: [["front html","back html"], ...], exercises: {...}, execLimit: 6000 })`
  — call once at the end of the lesson's inline script. Put lesson-specific widget code in the same inline script,
  using `CT.$`, `CT.$$`, `CT.esc`, `CT.highlight(src)` (returns highlighted HTML for code), `CT.runPython(code)`
  (returns Promise<{out, error}>), `CT.renderFigure(fig)`, `CT.reduced` (prefers-reduced-motion).

## Python runtime: Skulpt 1.2 (Python 3 subset in JS). Known limits — TEST every snippet
- `super().__init__(...)` with no arguments FAILS. Use `Parent.__init__(self, ...)` (the style the MIT lectures use)
  or `super(Child, self).__init__(...)`.
- `repr(0.1 + 0.2)` prints `0.3` (CPython prints 0.30000000000000004). For float-precision lessons, show
  `0.1 + 0.2 == 0.3` → False instead, which works, and mention it in prose.
- Speed: roughly 1M simple loop iterations per second. Keep simulations to ≲200k steps per run; set `data-limit`
  (ms) on heavy cells (max 20000). Default limit is 6000 ms.
- Available: math, random (seed, random, randint, choice, gauss, uniform, sample, shuffle), time, string, f-strings,
  classes, generators, exceptions, sets, dicts, recursion (keep depth < ~800).
- **Not available in Skulpt, so simulate instead:** `threading`, `multiprocessing`, `hashlib`, `hmac`, `sqlite3`,
  `json`, `flask`, `requests`, `pandas`, `os`, files. Simulate threads as explicit interleavings (lists of steps
  or generators driven by a seeded scheduler), networks as seeded random drops/duplicates on Python lists,
  crashes as an exception raised at step k, storage as dicts, checksums as a small hand-written hash
  (e.g. a polynomial rolling hash mod a large prime, explained as "a stand-in for SHA-256"), RPC as a client
  object calling a service object through a lossy "network" function. Say once in prose that the real lab
  uses the real library.
- No numpy/matplotlib. Instead `import pylab` (or `import numpy as np`, `import matplotlib.pyplot as plt` — all the same
  module) gives a teaching subset that draws real charts in the output: `plot(x, y, 'bo'/'r--'/'g-', label=)`,
  `scatter`, `bar`, `hist(values, bins=)`, `axhline`, `axvline`, `title`, `xlabel`, `ylabel`, `legend`, `xlim`, `ylim`,
  `semilogy`, `yscale('log')`, `figure()`, `show()`; numeric helpers on plain lists: `array` (returns a list — no
  elementwise arithmetic!), `arange`, `linspace`, `mean`, `std`, `var`, `median`, `sqrt`, `polyfit(x, y, deg)`,
  `polyval(coeffs, x)`. Always call `show()` to draw. Write list comprehensions instead of array math. Say once in
  the first Part 2 lesson that this is a browser subset of pylab and that full numpy behaves the same on these calls.

## Design rules
- Use only classes from course.css plus small inline styles; if you need lesson-specific CSS, put a `<style>` in the
  head using only the CSS tokens (`--paper --sheet --ink --muted --rule --accent --accent-soft --ok --ok-soft --bad
  --bad-soft --hl --code-bg --code-fg --s1..--s8 --display --body --mono`). Never a literal color that only works in
  one theme. Every widget must work at 390px width with no page-level horizontal scroll (wrap wide things in
  `.scroll-x`). SVG: use `viewBox` + `class="viz"`, color text via tokens.
- Respect reduced motion. Buttons are `<button type="button">`. No alert/confirm/prompt.
- Plain, direct copy. No emoji. No em-dash asides. Numbered markers only for real sequences.

## Testing (mandatory)
`node tools/test_lesson.js mNN --shots` (run from this `web/` folder) (after `npm install --no-save playwright skulpt@1.2.0`) runs every cell (auto-answers input() with 5), verifies every exercise's solution passes
its own cases, counts quizzes, checks overflow at 390px and reports JS/Python errors. Fix until: no `PY ERROR`
(except cells that deliberately demonstrate an error — keep those few and intentional), no JS errors, no OVERFLOW, every
exercise passes. Also check that each exercise's starter code does not pass. Look at `tools/shot-mNN-desk.png` and
`tools/shot-mNN-mob.png` once and fix anything visibly broken. Do not edit course.js, course.css, index.html or other
modules' files; if you believe the engine has a bug, describe it in your final report.
