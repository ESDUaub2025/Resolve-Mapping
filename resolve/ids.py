"""Stable pseudonymous respondent IDs.

The registry (private store: registry/respondent_ids.csv) maps a hash of the respondent's
identifying key to a random ID such as "CH-0EXAMP". IDs are assigned once and reused on every
rebuild, so they are stable across re-ordering or corrections of source rows, carry no
information about the person, and replace names and phone numbers everywhere outside the
private identity table.
"""
import csv
import hashlib
import secrets
from datetime import date

from .textnorm import key

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # no 0/O/1/I to avoid misreading
COLUMNS = ["instrument", "key_hash", "respondent_id", "assigned_on"]


def key_hash(instrument, values):
    parts = [instrument] + [key(v) or "" for v in values]
    if not any(parts[1:]):
        raise ValueError(f"empty respondent key for {instrument}")
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


class Registry:
    def __init__(self, path):
        self.path = path
        self.rows = {}
        self.new = 0
        if path.exists():
            with open(path, encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh):
                    self.rows[(row["instrument"], row["key_hash"])] = row

    def id_for(self, instrument, prefix, values):
        h = key_hash(instrument, values)
        row = self.rows.get((instrument, h))
        if row is None:
            taken = {r["respondent_id"] for r in self.rows.values()}
            while True:
                candidate = f"{prefix}-" + "".join(secrets.choice(ALPHABET) for _ in range(6))
                if candidate not in taken:
                    break
            row = {"instrument": instrument, "key_hash": h, "respondent_id": candidate,
                   "assigned_on": date.today().isoformat()}
            self.rows[(instrument, h)] = row
            self.new += 1
        return row["respondent_id"]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            for k in sorted(self.rows, key=lambda k: self.rows[k]["respondent_id"]):
                writer.writerow(self.rows[k])
