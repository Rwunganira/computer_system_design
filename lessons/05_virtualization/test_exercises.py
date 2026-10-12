import queue
import threading

import pytest

from course.testing import load_exercises

ex = load_exercises(__file__)  # also puts this lesson's folder on sys.path

import lab_pipeline  # noqa: E402


@pytest.fixture(scope="module")
def lab_files(tmp_path_factory):
    return lab_pipeline.write_lab_files(tmp_path_factory.mktemp("labs"), labs=3, per_lab=200)


def run_threads(n, target):
    threads = [threading.Thread(target=target) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


# Exercise 1: a counter that does not lose updates

def test_counter_counts_in_one_thread():
    counter = ex.SafeCounter()
    counter.increment()
    assert counter.value == 1


def test_counter_is_correct_under_many_threads():
    counter = ex.SafeCounter()
    run_threads(8, lambda: [counter.increment() for _ in range(200)])
    assert counter.value == 1600


# Exercise 2: a bounded buffer whose producers wait

def test_buffer_is_first_in_first_out():
    buf = ex.TimedBuffer(3)
    for item in "abc":
        assert buf.put(item) is True
    assert len(buf) == 3
    assert [buf.get(), buf.get(), buf.get()] == ["a", "b", "c"]


def test_full_buffer_put_times_out_without_dropping():
    buf = ex.TimedBuffer(2)
    buf.put("a"), buf.put("b")
    assert buf.put("c", timeout=0.05) is False
    assert len(buf) == 2 and buf.get() == "a" and buf.get() == "b"


def test_empty_buffer_get_times_out():
    with pytest.raises(queue.Empty):
        ex.TimedBuffer(2).get(timeout=0.05)


def test_producer_blocks_until_a_consumer_makes_room():
    buf = ex.TimedBuffer(1)
    buf.put("first")
    producer = threading.Thread(target=buf.put, args=("second",))
    producer.start()
    producer.join(timeout=0.1)
    assert producer.is_alive()          # still waiting: the buffer is full
    assert buf.get() == "first"         # make room ...
    producer.join(timeout=2)
    assert not producer.is_alive()      # ... and the producer finishes
    assert buf.get(timeout=1) == "second"


def test_buffer_in_the_lab_pipeline_loses_nothing(lab_files):
    paths, truth = lab_files
    valid, positives = lab_pipeline.run_pipeline(paths, ex.TimedBuffer(4), ex.SafeCounter())
    assert positives == truth
    assert valid == sum(1 for p in paths for line in open(p) if line.rstrip().endswith((",POS", ",NEG")))


# Exercise 3: processes instead of threads

def test_processes_count_every_positive(lab_files):
    paths, truth = lab_files
    assert ex.count_positives_with_processes(paths, workers=2) == truth
