"""Module 5 worked answers."""

import queue
import threading
import time
from collections import deque
from concurrent.futures import ProcessPoolExecutor

import lab_pipeline


class SafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            current = self.value
            time.sleep(0)
            self.value = current + 1

    # Why the unlocked version loses updates: thread A reads value 41 and is
    # paused; thread B reads 41 too, writes 42; A resumes and writes 42 as
    # well. Two positives were counted, the total went up by one. The read,
    # add and write are three separate steps, and any thread switch between
    # them lets another thread's update be overwritten. The lock makes the
    # three steps one before-or-after action.


class TimedBuffer:
    def __init__(self, capacity):
        self.items = deque()
        self.capacity = capacity
        self.lock = threading.Lock()
        self.not_full = threading.Condition(self.lock)
        self.not_empty = threading.Condition(self.lock)

    def put(self, item, timeout=None):
        with self.lock:
            if not self.not_full.wait_for(lambda: len(self.items) < self.capacity, timeout):
                return False
            self.items.append(item)
            self.not_empty.notify()
            return True

    def get(self, timeout=None):
        with self.lock:
            if not self.not_empty.wait_for(lambda: self.items, timeout):
                raise queue.Empty
            item = self.items.popleft()
            self.not_full.notify()
            return item

    def __len__(self):
        with self.lock:
            return len(self.items)


def count_positives_with_processes(paths, workers=2):
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return sum(pool.map(lab_pipeline.count_positives_in_file, paths))
    # What changed about shared state: each process has its own address space,
    # so there is nothing shared to race on, and no lock is needed. But nothing
    # is shared by accident either: a Counter created in the parent is *copied*
    # into each child, the children increment their copies, and the parent's
    # stays at 0. Results must travel back as messages (here, return values
    # that the pool pickles and sends to the parent), much like the client and
    # service in Module 4. Sharing on purpose needs multiprocessing.Value or a
    # Manager, which brings locks back.
