"""Little's law at a mass vaccination clinic, checked with a small simulation.

Little's law: in any stable system, on average

    N  =  X  x  R
    (people inside) = (throughput: people per minute) x (time each one spends inside)

It needs no assumptions about arrival patterns or service times. Here children
arrive at random (on average 90 an hour), each dose takes on average 2.5
minutes, and we try different numbers of vaccinators. For each run we *count*
how many people are in the clinic every half minute, and compare the average
count with X x R computed from arrival and departure times.

    python lessons/06_performance/clinic_queue.py
"""

import random
from statistics import mean

ARRIVALS_PER_MIN = 1.5      # 90 children an hour
DOSE_MINUTES = 2.5          # mean time a vaccinator spends per child
DAY_MINUTES = 8 * 60


def simulate(vaccinators, arrivals_per_min=ARRIVALS_PER_MIN, dose_minutes=DOSE_MINUTES,
             day_minutes=DAY_MINUTES, seed=6):
    """First come, first served with several vaccinators. Returns (arrive, leave) per child."""
    rng = random.Random(seed)
    free_at = [0.0] * vaccinators          # when each vaccinator next becomes free
    visits = []
    t = 0.0
    while True:
        t += rng.expovariate(arrivals_per_min)          # random (Poisson) arrivals
        if t > day_minutes:
            break                                      # the doors close; those inside are seen
        k = min(range(vaccinators), key=free_at.__getitem__)
        start = max(t, free_at[k])                     # wait if every vaccinator is busy
        free_at[k] = start + rng.expovariate(1 / dose_minutes)
        visits.append((t, free_at[k]))
    return visits


def count_inside(visits, step=0.5):
    """Average number of children inside, by looking every ``step`` minutes."""
    end = max(leave for _, leave in visits)
    samples = [sum(arrive <= s < leave for arrive, leave in visits)
               for s in (i * step for i in range(int(end / step)))]
    return mean(samples), max(samples)


def main():
    busy = ARRIVALS_PER_MIN * DOSE_MINUTES
    print(f"{ARRIVALS_PER_MIN * 60:.0f} children/hour, {DOSE_MINUTES} min per dose.")
    print(f"Little's law on the vaccinators alone: {ARRIVALS_PER_MIN} x {DOSE_MINUTES} "
          f"= {busy:.2f} vaccinators busy on average.\n")
    print("vaccinators  utilisation  minutes inside (R)  counted inside (N)  X x R    peak inside")
    for n in (3, 4, 5, 6, 8):
        visits = simulate(n)
        end = max(leave for _, leave in visits)
        throughput = len(visits) / end                 # children per minute, measured
        r = mean(leave - arrive for arrive, leave in visits)
        n_counted, peak = count_inside(visits)
        print(f"{n:>11}  {busy / n:>11.0%}  {r:>18.1f}  {n_counted:>18.1f}  {throughput * r:>5.1f}"
              f"  {peak:>12}")

    print("\nTwo lessons:")
    print(" 1. The counted average matches X x R every time: Little's law holds whatever the")
    print("    staffing. Knowing any two of N, X and R gives you the third.")
    print(" 2. Above 100% utilisation (3 vaccinators) the queue grows all day: children wait")
    print("    an hour. Near 100% (4) they keep up on average, yet the peak queue is long.")
    print("    Plan for utilisation well below 1.")
    print("    Waiting-area seats needed is N (plus room for the peak), not the arrival rate.")


if __name__ == "__main__":
    main()
