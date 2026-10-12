# Module 7. Networks

**Goal:** get correct weekly totals from rural clinics over a network that loses, duplicates and
reorders messages, and decide which layer should be responsible for "correct".

**Read in the book:** Chapter 7, *The Network as a System and as a System Component*: the network
layers (link, network, end-to-end), best-effort delivery, the end-to-end argument, and the
end-to-end layer's assurance of at-least-once and at-most-once delivery.

## Layers and what each promises

The book organises a network into three layers, each built on the one below:

- **Link layer**: moves a frame across one physical hop: a radio link from a phone to a cell
  tower. It may detect damaged frames, but it promises nothing beyond the hop.
- **Network layer**: forwards packets hop by hop from source to destination across many links.
  Its promise is deliberately weak: **best effort**. A packet may be lost (a queue overflowed),
  duplicated (a link resent it), delayed and reordered (it took another path), or, rarely,
  damaged.
- **End-to-end layer**: runs only in the two endpoints and turns best effort into whatever the
  application needs: reliable delivery, ordering, or nothing at all (a live video call prefers
  late frames dropped).

SMS is a good stand-in for the network layer. A clinic's text usually arrives; sometimes it does
not, sometimes it arrives twice, and two texts sent a minute apart can arrive in either order.

## Building reliable delivery

`sms_reports.py` adds the end-to-end mechanisms one at a time and watches the district totals:

1. **Fire and forget.** Each report is sent once and the office adds whatever arrives. Lost texts
   make the totals too low, duplicated texts too high. For surveillance, both are dangerous: a
   missed cholera report hides an outbreak, a doubled one raises a false alarm.
2. **Sequence numbers, acknowledgements and timeouts.** Each clinic numbers its reports. The office
   replies with an ACK naming the number. A clinic that gets no ACK within a **timeout** resends.
   That gives **at-least-once** delivery: every report eventually arrives. But "at least" means
   duplicates: if the ACK was lost, or only slow, the office receives a resend of a report it
   already has.
3. **Duplicate suppression.** The office remembers which (clinic, sequence number) pairs it has
   counted, acknowledges every copy (the clinic needs to hear back), and counts each only once:
   **at-most-once**. Together with step 2: exactly once, and totals are correct.

Reordering costs nothing here, because addition does not care about order. A protocol that needed
order (say, "dose 2" must follow "dose 1") would hold back early arrivals until the gap fills.

Choosing the timeout is a trade-off: too short and you resend reports that were merely slow,
wasting texts (and money); too long and a lost report waits before anyone notices.

## The end-to-end argument

A function such as "make sure the counts are right" can be implemented correctly only with the
knowledge of the application at the endpoints. Lower layers can help, but cannot finish the job:
the gateway can confirm each text arrived intact, yet it cannot know a nurse keyed 14 instead of 41,
or that the office's database dropped a row. So the end-to-end check is needed anyway. A check in
a lower layer is then justified only as a **performance** improvement (catching errors earlier,
fewer end-to-end retries), never as a replacement.

## In the running case

- **SurveilLite** gets its weekly counts from clinics, many on poor links. Exactly-once counting is
  what makes the incidence figures trustworthy.
- **VaxRecords** has the same problem with dose records from tablets that sync over mobile data: a
  resent "dose given" must not record a second dose (Module 10 returns to offline sync).

## Exercises

In `exercises.py`:

1. Add a checksum so garbled texts are detected, dropped without an ACK, and therefore resent.
2. Measure how many texts reliable delivery costs at 10%, 30% and 50% loss.
3. Use the end-to-end argument to decide who checks that clinic totals add up, then write the
   check.

## Run the example

```bash
python lessons/07_networks/sms_reports.py
pytest lessons/07_networks
```

Try changing `loss`, `duplicate` and the `timeout` in `send_reliably`, and watch the texts sent.
