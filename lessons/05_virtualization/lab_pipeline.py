"""A lab-results pipeline: producer threads, consumer threads, a bounded buffer.

Producers each read one lab's results file; consumers validate each result and
count the positives. Threads share one address space, so the only things that
keep them apart are the coordination tools we build here:

  1. A bounded buffer made by hand from a lock and two condition variables
     (sequence coordination: wait when full or empty, notify the other side).
  2. A shared positive-result counter, first without a lock (wrong totals),
     then with one ``with lock:`` (right totals).

    python lessons/05_virtualization/lab_pipeline.py
"""

import csv
import queue
import random
import tempfile
import threading
import time
from collections import deque
from pathlib import Path

DONE = None  # sentinel: "no more results", one per consumer


class BoundedBuffer:
    """A fixed-size FIFO shared by threads: put blocks when full, get blocks when empty."""

    def __init__(self, capacity):
        self.items = deque()
        self.capacity = capacity
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)   # producers wait here
        self.not_empty = threading.Condition(self.lock)  # consumers wait here

    def put(self, item):
        with self.lock:
            while len(self.items) >= self.capacity:  # `while`, not `if`: re-check after waking
                self.not_full.wait()                  # releases the lock while asleep
            self.items.append(item)
            self.not_empty.notify()                   # wake one waiting consumer

    def get(self):
        with self.lock:
            while not self.items:
                self.not_empty.wait()
            item = self.items.popleft()
            self.not_full.notify()                    # wake one waiting producer
            return item


class Counter:
    """A shared count. The pause between read and write invites a thread switch,
    which makes the race show up on every run instead of once in a while."""

    def __init__(self, locked):
        self.value = 0
        self.lock = threading.Lock() if locked else None

    def increment(self):
        if self.lock is None:
            self._read_modify_write()
        else:
            with self.lock:  # the whole fix
                self._read_modify_write()

    def _read_modify_write(self):
        current = self.value
        time.sleep(0)            # give up the processor, as a busy machine might
        self.value = current + 1


def write_lab_files(folder, labs=4, per_lab=500, seed=5):
    """Write one CSV of results per lab; return (paths, true number of positives)."""
    rng = random.Random(seed)
    paths, positives = [], 0
    for lab in range(1, labs + 1):
        path = Path(folder) / f"lab_{lab}.csv"
        with path.open("w", newline="") as f:
            out = csv.writer(f)
            out.writerow(["person_id", "test", "result"])
            for _ in range(per_lab):
                result = rng.choices(["POS", "NEG", "???"], [15, 80, 5])[0]  # some rows are garbage
                positives += result == "POS"
                out.writerow([f"P{rng.randrange(1, 2001):06d}", "measles IgM", result])
        paths.append(path)
    return paths, positives


def count_positives_in_file(path):
    """Positives in one file (used by the multiprocessing exercise)."""
    with open(path, newline="") as f:
        return sum(row["result"] == "POS" for row in csv.DictReader(f))


def run_pipeline(paths, buffer, counter, consumers=4):
    """Producers put rows into ``buffer``; consumers validate and count positives."""
    put, get = buffer.put, buffer.get     # our BoundedBuffer and queue.Queue share this interface
    stored = []

    def producer(path):
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                put(row)

    def consumer():
        while (row := get()) is not DONE:
            if row["result"] not in ("POS", "NEG"):
                continue                      # validation: reject garbage rows
            stored.append(row)                # list.append is atomic in CPython
            if row["result"] == "POS":
                counter.increment()

    producers = [threading.Thread(target=producer, args=(p,)) for p in paths]
    workers = [threading.Thread(target=consumer) for _ in range(consumers)]
    for t in producers + workers:
        t.start()
    for t in producers:
        t.join()
    for _ in workers:
        put(DONE)                             # one sentinel per consumer
    for t in workers:
        t.join()
    return len(stored), counter.value


def main():
    with tempfile.TemporaryDirectory() as folder:
        paths, truth = write_lab_files(folder)
        print(f"{len(paths)} lab files, {truth} positive results in them.\n")

        print("1. Hand-built bounded buffer (capacity 8), counter WITHOUT a lock")
        for run in range(1, 4):
            valid, positives = run_pipeline(paths, BoundedBuffer(8), Counter(locked=False))
            print(f"   run {run}: {valid} valid rows, counted {positives} positives "
                  f"({truth - positives} lost updates)")

        print("\n2. Same pipeline, counter WITH a lock")
        valid, positives = run_pipeline(paths, BoundedBuffer(8), Counter(locked=True))
        print(f"   {valid} valid rows, counted {positives} positives "
              f"({'correct' if positives == truth else 'WRONG'})")

        print("\n3. The standard library's queue.Queue(maxsize=8) in place of our buffer")
        valid, positives = run_pipeline(paths, queue.Queue(maxsize=8), Counter(locked=True))
        print(f"   {valid} valid rows, counted {positives} positives "
              f"({'correct' if positives == truth else 'WRONG'})")
        print("   queue.Queue is built the same way: one lock, conditions for not_full and not_empty.")


if __name__ == "__main__":
    main()
