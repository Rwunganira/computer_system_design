# Module 3. Naming

**Goal:** use the book's vocabulary for names precisely, and see how most "identity" bugs in
health data (duplicate patients, merged children, unreachable districts) are naming bugs.

**Read in the book:** the naming material at the end of Chapter 2 (names, binding and the naming
model), then Chapter 3, "The Design of Naming Schemes".

## The naming model

Systems use names everywhere: variable names, file paths, URLs, patient IDs, district codes. The
book describes them all with one small model:

- A **name** is a string used to refer to something. Its **value** is the thing it refers to.
- A **binding** is an association between a name and a value. Binding a name *is* the act of
  making it mean something; **unbinding** removes that meaning.
- A **context** is a set of bindings. A name only has a value in some context.
- **Resolution** (lookup) takes a name and a context and returns the value, or fails.

In Python, a dict is a context, `d[name] = value` binds, `del d[name]` unbinds and `d[name]`
resolves. That is why the example builds every context as a dictionary.

## Why context matters

Clinic A calls a child "P-0042". So does Clinic B, about a different child. Neither is wrong:
each local ID is bound in its own clinic's context. Problems start when a name escapes its
context: a report that says only "P-0042" with no clinic attached cannot be resolved.

The fix is to say which context to use. A **path name** like `clinic_a/P-0042` names the context
first and the patient second. Resolving it is a loop: look up `clinic_a` in the root context, get
a context back, look up `P-0042` in that. An **absolute** name is resolved from a fixed, well-known
root; a **relative** name is resolved from a **working context** (the clinic you are standing in),
so "P-0042" alone works fine inside Clinic C's own software.

## Pure and overloaded names

A **pure name** carries no information beyond identity: `P000042` tells you nothing about the
child. An **overloaded name** packs other meaning into the name: a district code inside a patient
ID, or "name plus date of birth" used as the key.

Overloading is tempting because the name is easy to read and you can check it against the person
in front of you. It fails in two ways the example shows with real numbers from the synthetic data:

- **Two different things share the name.** Two children called Paul Uwimana, both born on
  2022-04-03, get the same key; a dictionary keyed that way silently keeps one and their
  vaccination histories merge into one child who seems to have had most vaccines twice. In a real registry
  that drives a false coverage figure, or a missed dose.
- **The meaning changes but the name cannot.** A patient ID that embeds the district becomes
  wrong when the family moves. A pure ID stays right.

The same problem appears at the top of the system. `course.data.DISTRICTS` has two districts
named "Central" (North and South). A URL like `/districts/Central/cases` is a name; mapping it
through a `{district_name: district_id}` dict quietly binds "Central" to whichever row came last.
North Central, 182,000 people, has no URL at all. Nothing crashes; the dashboard is just wrong.
(Clinic names collide too: both districts have a "Central Health Centre 1". Look for it in the tests.)

## Indirection

An old saying, usually credited to David Wheeler, goes: "any problem in computer science can be
solved by another level of indirection." The book's version: let a name be bound to *another
name* rather than directly to the thing. Clinics bind their local IDs to registry IDs; only the
registry binds registry IDs to records. Then:

- a child who moves clinic gets a new local name bound to the same registry ID, and their history
  stays whole;
- a corrected birth date is fixed once, in the registry, and every clinic sees it;
- a clinic that is renamed keeps an **alias** from its old name to its new one, so last year's
  reports still resolve (Exercise 2).

The cost is an extra lookup, and a new failure: aliases can form a loop.

## Exercises

In `exercises.py`:

1. Make district names unambiguous without breaking existing URLs: resolve by `district_id`,
   qualify by region, and answer an ambiguous name with *choices* instead of a guess.
2. Add an alias layer so a renamed clinic's old names still resolve.
3. Find registry IDs bound to records with conflicting birth dates: the symptom of an overloaded
   name merging two children.

## Run the example

```bash
python lessons/03_naming/patient_resolver.py
pytest lessons/03_naming
```

The Flask part uses `app.test_client()`, which calls the app in-process, so no port is opened.
