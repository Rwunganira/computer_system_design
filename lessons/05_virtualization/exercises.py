"""Module 5 exercises. Complete each TODO, then run: pytest lessons/05_virtualization"""

import queue
import threading
import time


class SafeCounter:
    """A positive-result counter that many consumer threads can share.

    Exercise 1. First run ``lab_pipeline.py`` and watch the unlocked counter
    lose updates. Then make ``increment`` correct. Keep the read, the pause and
    the write exactly as given; add a lock so no other thread can run the same
    steps in between.
    """

    def __init__(self):
        self.value = 0
        # TODO: create a lock

    def increment(self):
        # TODO: hold a lock around these three steps.
        raise NotImplementedError
        current = self.value
        time.sleep(0)
        self.value = current + 1

    # TODO (not tested): in a comment, write down why the unlocked version
    # loses updates. Which two threads, doing which steps, in which order?


class TimedBuffer:
    """A bounded buffer whose producers wait (instead of dropping results) when it is full.

    Exercise 2. The lab's first pipeline used ``put_nowait`` and threw results
    away whenever the buffer was full. Build the buffer yourself from one lock
    and two condition variables, as in ``lab_pipeline.BoundedBuffer``, and add
    timeouts:

    - ``put(item, timeout=None)`` waits while the buffer is full. With
      ``timeout=None`` it waits as long as it takes and returns True. With a
      timeout in seconds, it returns False if there is still no room by then,
      and leaves the buffer unchanged. Never drop an item silently.
    - ``get(timeout=None)`` waits while the buffer is empty and returns the
      oldest item (first in, first out). If ``timeout`` runs out first, it raises
      ``queue.Empty``.
    - ``len(buffer)`` is the number of items waiting.

    Hint: ``Condition.wait_for(predicate, timeout)`` returns False on timeout.
    """

    def __init__(self, capacity):
        # TODO
        raise NotImplementedError

    def put(self, item, timeout=None):
        # TODO
        raise NotImplementedError

    def get(self, timeout=None):
        # TODO
        raise NotImplementedError

    def __len__(self):
        # TODO
        raise NotImplementedError


def count_positives_with_processes(paths, workers=2):
    """Exercise 3. The total number of positive results in ``paths``, counted by
    ``workers`` separate processes, one file at a time.

    Use ``concurrent.futures.ProcessPoolExecutor`` (or ``multiprocessing.Pool``)
    with ``lab_pipeline.count_positives_in_file`` as the worker. A child process
    must be able to import the worker function by name, which is why it lives in
    ``lab_pipeline`` and not here. Each child returns a number and the parent
    adds them up.
    """
    # TODO
    raise NotImplementedError
    # TODO (not tested): in a comment, note what changed about shared state.
    # What would happen if each child called increment() on one Counter
    # created in the parent?
