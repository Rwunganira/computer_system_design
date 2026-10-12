"""Module 7 worked answers."""

import zlib
from collections import Counter

import sms_reports


def add_checksum(text):
    return f"{text}#{zlib.crc32(text.encode())}"


def verify(wire):
    text, sep, checksum = wire.rpartition("#")
    if not sep or not checksum.isdigit():
        return None
    return text if zlib.crc32(text.encode()) == int(checksum) else None


def texts_sent(messages, loss_rates):
    sent = {}
    for loss in loss_rates:
        up = sms_reports.SmsChannel(loss=loss, seed=2)
        down = sms_reports.SmsChannel(loss=loss, seed=3)
        sms_reports.send_reliably(messages, up, down)
        sent[loss] = up.sent
    # Each try succeeds only if report and ACK both survive: (1 - p) ** 2.
    # So expect about 1 / (1 - p) ** 2 sends per report: 1.2 at 10%, 2 at 30%,
    # 4 at 50%. The simulation gives about 1.2, 1.9 and 3.7 for 480 reports:
    # slightly less, because a channel duplicate is a free second chance.
    return sent


def where_to_check():
    """District office.

    Only the endpoint that uses the numbers can know they are right. The
    gateway can confirm that each SMS arrived intact, but not that the clinic
    keyed the right count, that the office's database stored it, or that a
    bug further along did not drop a row. The office must check the totals
    anyway, so a check in the gateway is at most a performance optimisation
    (fewer resends), never a substitute.
    """
    return "district office"


def clinics_with_wrong_totals(records, clinic_totals):
    received = Counter()
    for clinic_id, _week, cases in records:
        received[clinic_id] += cases
    return sorted(c for c, total in clinic_totals.items() if received.get(c) != total)
