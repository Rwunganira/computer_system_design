"""A tiny interpreter for case definitions, run two ways: record by record, and over a DataFrame.

A case definition is written as text, for example

    fever AND (rash OR cough) AND age < 15

The interpreter tokenizes the text, parses it into a tree, then evaluates the tree against
each patient record. The same tree also runs over a whole pandas DataFrame at once: one
abstraction (an interpreter for rules) with two implementations.
"""

import operator
import random
import re
import time

import pandas as pd

from course.data import DISTRICTS

# --- 1. Tokenize: text -> list of tokens -------------------------------------------------

TOKEN = re.compile(r"\s*(?:(\d+)|([A-Za-z_]\w*)|(<=|>=|==|!=|<|>)|([()]))")
KEYWORDS = {"AND", "OR", "NOT", "WITHIN", "DAYS", "OF"}


def tokenize(text):
    """Split a rule into (kind, value) tokens: num, name, keyword, cmp or paren."""
    tokens, pos, text = [], 0, text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m:
            raise SyntaxError(f"unexpected character at {pos}: {text[pos:]!r}")
        num, word, cmp, paren = m.groups()
        if num:
            tokens.append(("num", int(num)))
        elif word:
            tokens.append(("keyword", word.upper()) if word.upper() in KEYWORDS else ("name", word))
        else:
            tokens.append(("cmp", cmp) if cmp else ("paren", paren))
        pos = m.end()
    return tokens


# --- 2. Parse: tokens -> tree of tuples ---------------------------------------------------
#   or_expr  := and_expr (OR and_expr)*
#   and_expr := atom (AND atom)*
#   atom     := '(' or_expr ')' | name cmp num | name

class Parser:
    def __init__(self, text):
        self.tokens, self.i = tokenize(text), 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else (None, None)

    def take(self, kind, value=None):
        tok = self.peek()
        if tok[0] != kind or (value is not None and tok[1] != value):
            raise SyntaxError(f"expected {value or kind}, got {tok[1] or 'end of rule'!r}")
        self.i += 1
        return tok[1]

    def parse(self):
        tree = self.parse_or()
        if self.i != len(self.tokens):
            raise SyntaxError(f"unexpected {self.peek()[1]!r}")
        return tree

    def parse_or(self):
        node = self.parse_and()
        while self.peek() == ("keyword", "OR"):
            self.take("keyword", "OR")
            node = ("or", node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_atom()
        while self.peek() == ("keyword", "AND"):
            self.take("keyword", "AND")
            node = ("and", node, self.parse_atom())
        return node

    def parse_atom(self):
        if self.peek() == ("paren", "("):
            self.take("paren", "(")
            node = self.parse_or()
            self.take("paren", ")")
            return node
        name = self.take("name")
        if self.peek()[0] == "cmp":
            op = self.take("cmp")
            return ("cmp", op, name, self.take("num"))
        return ("var", name)


def parse(text):
    return Parser(text).parse()


# --- 3. Evaluate: the interpreter loop ----------------------------------------------------

CMP = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge,
       "==": operator.eq, "!=": operator.ne}


class RecordInterpreter:
    """Evaluates a tree against one record (a dict) at a time."""

    trace = False

    def evaluate(self, node, record):
        # Fetch the node, decode its kind, execute the matching method.
        kind = node[0]
        result = getattr(self, "eval_" + kind)(node, record)
        if self.trace:
            print(f"    exec {kind:<4} {node[1:] if kind in ('var', 'cmp') else ''} -> {result}")
        return result

    def eval_and(self, node, record):
        return self.evaluate(node[1], record) and self.evaluate(node[2], record)

    def eval_or(self, node, record):
        return self.evaluate(node[1], record) or self.evaluate(node[2], record)

    def eval_var(self, node, record):
        return bool(record[node[1]])

    def eval_cmp(self, node, record):
        _, op, name, value = node
        return CMP[op](record[name], value)

    def before_each(self, record):
        """Hook called before each record; stateful operators can use it."""

    def run(self, tree, records):
        """The outer loop: one result per record, in order."""
        results = []
        for record in records:
            self.before_each(record)
            results.append(self.evaluate(tree, record))
        return results


class FrameInterpreter:
    """Same tree, different machine: evaluates a whole DataFrame column-wise at once."""

    def evaluate(self, node, df):
        return getattr(self, "eval_" + node[0])(node, df)

    def eval_and(self, node, df):
        return self.evaluate(node[1], df) & self.evaluate(node[2], df)

    def eval_or(self, node, df):
        return self.evaluate(node[1], df) | self.evaluate(node[2], df)

    def eval_var(self, node, df):
        return df[node[1]].astype(bool)

    def eval_cmp(self, node, df):
        _, op, name, value = node
        return CMP[op](df[name], value)


def line_list(n=20_000, seed=3):
    """Synthetic patient records with symptoms, as a DataFrame."""
    rng = random.Random(seed)
    return pd.DataFrame([{"person_id": f"P{i:06d}", "district_id": rng.choice(list(DISTRICTS.district_id)),
                          "age": rng.randrange(60), "fever": rng.random() < 0.3,
                          "rash": rng.random() < 0.1, "cough": rng.random() < 0.25}
                         for i in range(1, n + 1)])


def main():
    rule = "fever AND (rash OR cough) AND age < 15"
    print(f"Rule: {rule}\n\nTokens: {tokenize(rule)}\n\nTree:   {parse(rule)}\n")

    df, tree = line_list(), parse(rule)
    first = df[df.fever & df.rash & (df.age < 15)].iloc[0].to_dict()
    print(f"Tracing one record: {first}")
    tracer = RecordInterpreter()
    tracer.trace = True
    print(f"  => {tracer.evaluate(tree, first)}\n")

    t0 = time.perf_counter()
    row_results = RecordInterpreter().run(tree, df.to_dict("records"))
    t1 = time.perf_counter()
    frame_results = FrameInterpreter().evaluate(tree, df)
    t2 = time.perf_counter()
    print(f"Record interpreter: {sum(row_results):>5} cases of {len(df):,} in {t1 - t0:.3f} s")
    print(f"Frame interpreter:  {int(frame_results.sum()):>5} cases of {len(df):,} in {t2 - t1:.3f} s")
    print(f"Same answer from both implementations: {list(frame_results) == row_results}\n")

    print("Changing the case definition is editing data, not code:")
    for text in ["fever AND rash", "fever AND rash AND age < 5", "fever AND rash OR cough"]:
        print(f"  {text:<28} -> {int(FrameInterpreter().evaluate(parse(text), df).sum()):>5} cases")

    print("  (AND binds tighter than OR, so the last rule is (fever AND rash) OR cough)")
    print("\nA malformed rule is rejected before it touches any data:")
    try:
        parse("fever AND (rash OR")
    except SyntaxError as err:
        print(f"  SyntaxError: {err}")


if __name__ == "__main__":
    main()
