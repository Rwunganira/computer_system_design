"""Module 7 exercises. Complete each TODO, then run: pytest lessons/07_networks"""

import sms_reports  # noqa: F401  (the example: SmsChannel, send_reliably, ...)


# ---------------------------------------------------------------------------
# Exercise 1. Detect corrupted messages.
#
# send_reliably(..., encode=add_checksum, decode=verify) wraps every message on
# the wire. A message that fails verify() is dropped without an ACK, so the
# sender's timeout resends it. Detection plus retransmission = correction.
# ---------------------------------------------------------------------------

def add_checksum(text):
    """Return ``text`` with a checksum appended, e.g. "DATA|C01|1|2026-01-05|3#417".

    Any single changed character in the result must be detected by verify().
    A sum of character codes modulo a number larger than any one change, or
    zlib.crc32, both work.
    """
    # TODO
    raise NotImplementedError


def verify(wire):
    """Return the original text if the checksum matches, otherwise None.

    Must not raise on garbage: a corrupted message may have lost its "#" or
    have letters where the checksum digits were.
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 2. What does reliability cost?
# ---------------------------------------------------------------------------

def texts_sent(messages, loss_rates):
    """For each loss rate, send ``messages`` reliably and count the texts sent.

    Use sms_reports.send_reliably with up = SmsChannel(loss=loss, seed=2) and
    down = SmsChannel(loss=loss, seed=3) (ACKs are lost too). Return
    {loss: up.sent}.

    Then think: a report gets through only when both the report and its ACK
    survive. At loss p, about how many sends per report would you expect?
    """
    # TODO
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Exercise 3. The end-to-end argument.
#
# Each clinic also sends a monthly summary: the total cases it reported. Who
# should compare that total with what was received: the SMS gateway (which
# already does sequence numbers and ACKs), or the district office application
# that computes incidence?
# ---------------------------------------------------------------------------

def where_to_check():
    """Return "gateway" or "district office".

    Write your argument here, in two or three sentences, using the end-to-end
    argument.
    """
    # TODO
    raise NotImplementedError


def clinics_with_wrong_totals(records, clinic_totals):
    """Compare what the office received with what each clinic says it sent.

    ``records`` is a list of (clinic_id, week, cases) the office accepted.
    ``clinic_totals`` is {clinic_id: total cases the clinic reported}.
    Return a sorted list of clinic_ids whose received total differs. A clinic
    with no records at all is wrong even if its total is 0: silence is not a
    report of zero cases.
    """
    # TODO
    raise NotImplementedError
