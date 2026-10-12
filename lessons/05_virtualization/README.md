# Module 5. Virtualization

**Goal:** run many activities inside one computer without letting them trip over each other: find a
race condition, fix it with a lock, and pass work between threads with a bounded buffer.

**Read in the book:** Chapter 5, "Enforcing Modularity with Virtualization".

## One computer, many virtual ones

Module 4 enforced modularity by putting the client and the service on separate computers that talk
only by messages. That is expensive if you need a computer per module. **Virtualization** gives
each module the *illusion* of its own computer while they share one physical machine. The book
virtualizes the three fundamental abstractions from Chapter 2:

| Real thing | Virtual version | What it gives each module |
|---|---|---|
| processor (interpreter) | **thread** | its own processor, which the scheduler shares out |
| memory | **virtual memory** (address spaces) | its own memory, which others cannot touch |
| communication link | **bounded buffer** | its own message channel to another module |

A *process* in your operating system is roughly a thread plus its own address space. Two processes
cannot corrupt each other's memory, so the modularity is enforced. Threads inside one process share
one address space: cheap and convenient, but all the protection is gone, and coordination is your
job.

## Race conditions and locks

Counting positive lab results looks like one step, `count += 1`, but it is three: read the count,
add one, write it back. If the scheduler switches threads between the read and the write, two
threads can both read 41 and both write 42. One positive vanishes. This is a **race condition**:
the result depends on the timing of the threads, so it is wrong *sometimes*, which is worse than
always. A surveillance count that is slightly low on some runs is the kind of error nobody notices
until an outbreak is missed.

The fix is a **lock**: `with lock:` around the read-modify-write makes those steps happen
*before-or-after* any other thread's, never interleaved. The book builds locks from an atomic
hardware instruction; in Python, `threading.Lock` does it for you. (Chapter 9 comes back to
before-or-after atomicity in depth.)

Python's global interpreter lock does *not* save you here: it guarantees that one bytecode runs at a
time, not that your three steps do. The example adds a `time.sleep(0)` between read and write so
the race shows up on every run instead of once a week in production.

## Sequence coordination: the bounded buffer

Lab files arrive faster than consumers can validate them, or slower. Producers and consumers need a
buffer between them that holds at most *N* results: a **bounded buffer**. Two rules:

- a producer that finds the buffer **full** must wait until a consumer takes something;
- a consumer that finds it **empty** must wait until a producer adds something.

Waiting by spinning in a loop wastes the processor. Instead, a thread **waits** on a *condition
variable* (which releases the lock while it sleeps) and the other side **notifies** it when the
state changes. The book calls this sequence coordination, built from *wait* and *notify*. The
example builds a bounded buffer from one lock and two condition variables, `not_full` and
`not_empty`, then swaps in Python's `queue.Queue`, which is built exactly the same way. Use
`queue.Queue` in real code; build it once by hand so you know what it does.

Things to notice in `lab_pipeline.py`:

- `while`, not `if`, around each `wait()`: a woken thread must re-check the condition, because
  another thread may have got there first.
- The sentinel `DONE`, one per consumer, is how producers say "no more results".
- A full buffer slows the producers down instead of losing results. That pushback is called
  *backpressure*, and it is the same idea as the client backing off in Module 4.

## Exercises

1. `SafeCounter`: run the unlocked version until the count is wrong, write down why, then fix it.
2. `TimedBuffer`: make producers block when the buffer is full instead of dropping results, with
   optional timeouts on `put` and `get`.
3. `count_positives_with_processes`: replace threads with processes (`multiprocessing`) and note what
   changes about shared state. The written parts of exercises 1 and 3 are for you; pytest checks
   only the code.

## Run the example

```bash
python lessons/05_virtualization/lab_pipeline.py    # race, then the lock, then queue.Queue (about 1 s)
pytest lessons/05_virtualization
```
