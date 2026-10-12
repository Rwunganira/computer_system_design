"""Weekly case counts over an unreliable SMS channel, made reliable end to end.

Rural clinics text their weekly cholera counts to the district office. The SMS
network is a best-effort network: a message may be lost, delivered twice, or
overtake an earlier one. Time is simulated in rounds (no real sleeping), and
the channel's misbehaviour comes from a seeded random generator, so every run
is the same.

    python lessons/07_networks/sms_reports.py
"""

import random
from collections import Counter
from dataclasses import dataclass, field

from course.data import case_reports, clinics

DISTRICT_OF = dict(zip(clinics().clinic_id, clinics().district_id))


class SmsChannel:
    """One direction of an SMS link. Loses, duplicates, delays (so reorders)
    and optionally corrupts messages."""

    def __init__(self, loss=0.2, duplicate=0.1, corrupt=0.0, max_delay=3, seed=1):
        self.rng = random.Random(seed)
        self.loss, self.duplicate, self.corrupt, self.max_delay = loss, duplicate, corrupt, max_delay
        self.now = 0                # the current round
        self.sent = 0               # messages handed to the channel (what the clinic pays for)
        self.in_flight = []         # (arrival round, text)

    def send(self, text):
        self.sent += 1
        if self.rng.random() < self.loss:
            return                                          # lost
        copies = 2 if self.rng.random() < self.duplicate else 1
        for _ in range(copies):
            if self.rng.random() < self.corrupt:            # flip one character to a digit
                i = self.rng.randrange(len(text))
                text = text[:i] + self.rng.choice("0123456789".replace(text[i], "")) + text[i + 1:]
            self.in_flight.append((self.now + self.rng.randint(1, self.max_delay), text))

    def deliver(self):
        """Advance one round; return the messages that arrive, in any order."""
        self.now += 1
        arriving = [text for t, text in self.in_flight if t <= self.now]
        self.in_flight = [(t, text) for t, text in self.in_flight if t > self.now]
        self.rng.shuffle(arriving)
        return arriving


def as_messages(reports):
    """Report rows -> (clinic_id, week, cases), the payload a clinic sends."""
    return [(r.clinic_id, str(r.week_start), r.cases) for r in reports.itertuples()]


def district_totals(records):
    totals = Counter()
    for clinic_id, _week, cases in records:
        totals[DISTRICT_OF[clinic_id]] += cases
    return dict(sorted(totals.items()))


def send_naively(messages, channel):
    """Fire and forget: each report sent once, the office adds up whatever arrives."""
    for clinic_id, week, cases in messages:
        channel.send(f"{clinic_id}|{week}|{cases}")
    records = []
    while channel.in_flight:
        for text in channel.deliver():
            clinic_id, week, cases = text.split("|")
            records.append((clinic_id, week, int(cases)))
    return records


def parse(text, n):
    """Split a message into ``n`` fields, or None if it is rejected or malformed."""
    if text is None or text.count("|") != n - 1:
        return None
    fields = text.split("|")
    if (fields[0] not in ("DATA", "ACK") or fields[1] not in DISTRICT_OF
            or not (fields[2].isdigit() and fields[-1].isdigit())):
        return None
    return fields


@dataclass
class Result:
    records: list = field(default_factory=list)   # what the office accepted
    rounds: int = 0
    retransmissions: int = 0
    duplicates_dropped: int = 0
    corrupted_dropped: int = 0


def send_reliably(messages, up, down, timeout=8, suppress_duplicates=True,
                  encode=lambda text: text, decode=lambda text: text, max_rounds=10_000):
    """Sequence numbers + acknowledgements + timeouts + duplicate suppression.

    ``up`` carries reports to the office, ``down`` carries ACKs back. Each
    clinic numbers its own messages 1, 2, 3... The office acknowledges every
    copy it receives (the first ACK may have been lost), but counts each
    (clinic, seq) only once. ``encode``/``decode`` wrap every message on the
    wire; ``decode`` returns None for a message it rejects.
    """
    result = Result()
    next_seq = Counter()
    unacked = {}                 # (clinic, seq) -> text, kept until ACKed
    for clinic_id, week, cases in messages:
        next_seq[clinic_id] += 1
        unacked[(clinic_id, next_seq[clinic_id])] = f"DATA|{clinic_id}|{next_seq[clinic_id]}|{week}|{cases}"
    last_sent = {}               # (clinic, seq) -> round it was last sent
    seen = set()                 # office side: (clinic, seq) already counted

    for now in range(max_rounds):
        # Clinics: send new messages, resend any whose ACK is overdue.
        for key, text in unacked.items():
            if key not in last_sent or now - last_sent[key] >= timeout:
                result.retransmissions += key in last_sent
                up.send(encode(text))
                last_sent[key] = now
        # District office: accept, acknowledge, suppress duplicates.
        for wire in up.deliver():
            fields = parse(decode(wire), 5)
            if fields is None:
                result.corrupted_dropped += 1      # no ACK, so the clinic will resend
                continue
            _, clinic_id, seq, week, cases = fields
            down.send(encode(f"ACK|{clinic_id}|{seq}"))
            if suppress_duplicates and (clinic_id, seq) in seen:
                result.duplicates_dropped += 1
                continue
            seen.add((clinic_id, seq))
            result.records.append((clinic_id, week, int(cases)))
        # Clinics: an ACK means "delivered", stop resending.
        for wire in down.deliver():
            fields = parse(decode(wire), 3)
            if fields is not None:
                _, clinic_id, seq = fields
                unacked.pop((clinic_id, int(seq)), None)
        if not unacked:
            result.rounds = now + 1
            return result
    raise RuntimeError(f"gave up after {max_rounds} rounds with {len(unacked)} reports unacknowledged")


def main():
    reports = case_reports()
    messages = as_messages(reports[reports.disease == "cholera"])
    truth = district_totals(messages)
    print(f"{len(messages)} cholera reports from 40 clinics over 12 weeks.")
    print("Channel: 20% lost, 10% duplicated, delays of 1-3 rounds (so reordered).\n")

    naive = district_totals(send_naively(messages, SmsChannel(seed=1)))
    no_dedup = send_reliably(messages, SmsChannel(seed=2), SmsChannel(seed=3), suppress_duplicates=False)
    up = SmsChannel(seed=2)
    full = send_reliably(messages, up, SmsChannel(seed=3))

    print("district   true  fire&forget  +seq/ack/retry  +drop duplicates")
    for d in truth:
        print(f"{d:<8} {truth[d]:>6} {naive.get(d, 0):>12} "
              f"{district_totals(no_dedup.records).get(d, 0):>15} {district_totals(full.records)[d]:>17}")

    print("\nFire and forget: lost reports make totals too low, duplicated ones too high.")
    print("Retransmission fixes losses, but every copy now counts: channel duplicates, and")
    print("resends whose first copy arrived but whose ACK was lost or slow. "
          f"{len(no_dedup.records) - len(messages)} extra reports counted.")
    print(f"Full protocol: {up.sent} texts for {len(messages)} reports "
          f"({full.retransmissions} retransmissions), {full.duplicates_dropped} duplicates dropped, "
          f"done in {full.rounds} rounds.")
    print(f"Totals correct: {district_totals(full.records) == truth}\n")

    garbled = send_reliably(messages, SmsChannel(corrupt=0.05, seed=2), SmsChannel(seed=3))
    print("Now let 5% of texts be garbled in transit (one character changed):")
    print(f"Totals correct: {district_totals(garbled.records) == truth}  <- nothing detects it. "
          "Exercise 1 adds a checksum.")


if __name__ == "__main__":
    main()
