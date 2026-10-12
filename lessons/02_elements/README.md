# Module 2. Elements of computer system organization

**Goal:** see every system, however large, as built from three kinds of parts: memories,
interpreters and communication links. Then build one of each kind's behaviour in miniature.

**Read in the book:** Chapter 2, "Elements of Computer System Organization", the parts on the
three fundamental abstractions (memory, interpreters, communication links). Leave the naming
material at the end of the chapter for Module 3.

## Three abstractions

Saltzer and Kaashoek argue that you can describe almost any computer system with three
abstractions. Each hides a great deal of mechanism behind a very small interface.

| Abstraction | Interface | In SurveilLite and VaxRecords |
|---|---|---|
| **Memory** | `READ(name)`, `WRITE(name, value)` | a SQLite table, a CSV file, a Python dict, a dose record |
| **Interpreter** | an instruction reference, a repertoire, an environment | the CPU, the Python interpreter, Flask's request loop, a case-definition evaluator |
| **Communication link** | `SEND(link, message)`, `RECEIVE(link)` | HTTP between dashboard and API, an SMS from a rural clinic |

The value of the abstraction is that you can swap the implementation. A "memory" might be RAM, a
disk, or a table on another continent; the code that calls `READ` should not have to care. (It
will care about speed and failure, which is what most of the book is about.)

## Memory, and why the last write does not always win

The simplest promise a memory makes is **read/write coherence**: a `READ` returns the value of the
most recent `WRITE` to that name. With one user and one copy, that is easy. It gets hard when:

- **Two writers do read, modify, write without coordination.** Clinic A and Clinic B both read a
  child's dose list, each appends a dose, each writes back. Each write is perfectly coherent, yet
  one clinic's dose disappears: a **lost update**. "The last write wins" is true of the memory and
  wrong for the epidemiologist, because the last write was based on a stale read.
- **There are several copies** (a cache, a replica on an offline tablet). Now "most recent" needs
  a definition. Chapter 10 and Module 10 return to this.
- **A write is not atomic.** A write of a large record might be interrupted half way (Module 9).

The book's term for the property we actually want here is **before-or-after atomicity**: one
clinic's update should happen entirely before or entirely after the other's. Exercise 3 shows the
loss, then fixes it with a version check (write only if nobody wrote since you read).

## Interpreters

An interpreter is a loop that never stops:

1. **Fetch** the next instruction (from the instruction reference, like a program counter),
2. **Decode** it: what kind of instruction is it?
3. **Execute** it, possibly changing the environment (registers, memory),
4. repeat.

A processor does this with machine instructions. The Python interpreter does it with bytecode. And
any time you write rules *as data* and a program that follows them, you have built an interpreter.

Case definitions are a natural fit. A WHO-style definition such as "fever AND (rash OR cough) AND
age < 15" changes when an outbreak investigation refines it. If it is hard-coded as a Python `if`,
every change needs a developer and a deployment. If it is text that SurveilLite interprets, an
epidemiologist can change it, and the system can store, compare and audit versions of it.

`case_definition.py` builds the interpreter in three steps:

- **tokenize** turns the text into tokens: names, keywords, numbers, operators, parentheses;
- **parse** turns tokens into a tree, so that `AND` binds tighter than `OR`;
- **evaluate** walks the tree. Each node is fetched, its kind decoded (`"and"`, `"or"`, `"var"`,
  `"cmp"`), and the matching `eval_` method executed. `run` is the outer loop over records.

The *same tree* then runs on a second interpreter, `FrameInterpreter`, which executes each node
over an entire pandas column at once. One abstraction, two implementations, the same answers, very
different speed. This is the book's point about abstraction: the rule's meaning is fixed by the
interface, the implementation is free to change.

Some instructions need the interpreter to **keep state** between steps, as a processor keeps
registers. Exercise 2 adds `WITHIN 14 DAYS OF onset`, whose answer for one visit depends on the
first visit the interpreter saw for that patient.

## Communication links

A link moves messages between places that do not share memory. Unlike a memory, it can lose,
delay, duplicate and reorder what you give it. This module only names the abstraction; Modules 4
(clients and services) and 7 (networks) build on it.

## Exercises

In `exercises.py`, each one extends the example by subclassing, so `case_definition.py` stays as is:

1. Add a `NOT` operator (parser and interpreter).
2. Add `WITHIN n DAYS OF onset`, an operator that needs the interpreter to remember earlier records.
3. Show that two clinics writing the same record without coordination lose an update, then fix it.

## Run the example

```bash
python lessons/02_elements/case_definition.py
pytest lessons/02_elements
```
