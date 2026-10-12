"""Detect silent corruption of stored case counts with SHA-256 checksums.

A disk, a USB stick or a sync tool can change a byte without reporting any
error. Reading the file "succeeds" and the dashboard shows a wrong number. A
checksum stored next to the data turns that silent fault into a detected error.
"""

import hashlib
import tempfile
from pathlib import Path

from course.data import case_reports


class CorruptionError(Exception):
    """The data on disk does not match its checksum."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def save(folder, name, data):
    """Write ``data`` (bytes) to folder/name and its checksum to folder/name.sha256."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(data)
    (folder / f"{name}.sha256").write_text(sha256(data))


def load_unchecked(folder, name):
    """Read the bytes and trust them. This is what most code does."""
    return (Path(folder) / name).read_bytes()


def load(folder, name):
    """Read the bytes and verify them: fail fast instead of returning bad data."""
    data = load_unchecked(folder, name)
    expected = (Path(folder) / f"{name}.sha256").read_text().strip()
    if sha256(data) != expected:
        raise CorruptionError(f"{Path(folder) / name}: checksum mismatch")
    return data


def flip_bit(path, offset, mask=0x01):
    """Simulate a hardware fault: flip one bit of one byte in a file."""
    raw = bytearray(Path(path).read_bytes())
    raw[offset] ^= mask
    Path(path).write_bytes(bytes(raw))


def weekly_cholera_csv(district_id="S-COA"):
    """Weekly cholera totals for one district, as CSV bytes."""
    r = case_reports()
    weekly = r[(r.disease == "cholera") & (r.district_id == district_id)].groupby("week_start").cases.sum()
    return weekly.to_csv().encode()


def total_cases(csv_bytes):
    """Sum the second column of the CSV (skipping the header)."""
    lines = csv_bytes.decode().strip().splitlines()[1:]
    return sum(int(line.split(",")[1]) for line in lines)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        primary, backup = Path(tmp) / "primary", Path(tmp) / "backup"
        data = weekly_cholera_csv()
        save(primary, "s-coa_cholera.csv", data)
        save(backup, "s-coa_cholera.csv", data)
        print(f"Stored S-COA weekly cholera counts on two replicas, total = {total_cases(data)} cases")

        # A bit flips in the last digit of the file (the latest week's count).
        # XOR 0x01 turns a digit into another digit, so the CSV still parses.
        path = primary / "s-coa_cholera.csv"
        offset = data.rstrip().rindex(b",") + 1
        flip_bit(path, offset)
        print("\nOne bit flipped on the primary disk. No error was reported.")

        print("\n1. Reading without a checksum (the silent failure):")
        print(f"   total = {total_cases(load_unchecked(primary, 's-coa_cholera.csv'))} cases"
              "  <- wrong, and nothing tells us")

        print("\n2. Reading with a checksum (fault becomes a detected error):")
        try:
            load(primary, "s-coa_cholera.csv")
        except CorruptionError as e:
            print(f"   CorruptionError: {e.args[0].split(': ')[1]}")

        print("\n3. Redundancy masks it: fall back to the backup replica:")
        good = load(backup, "s-coa_cholera.csv")
        print(f"   total = {total_cases(good)} cases  <- correct")
        print("\n(Exercise 3: make the reader also repair the bad replica.)")


if __name__ == "__main__":
    main()
