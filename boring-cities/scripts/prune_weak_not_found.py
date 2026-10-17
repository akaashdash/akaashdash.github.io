"""Drop weak 'searched, nothing found' entries so those activities stay in the unsearched pool.

A not_found entry is weak when its note says only a Meetup/Eventbrite keyword page loaded (these pages
match loosely and mostly list events) or calls itself weak evidence, and does not mention a real search.
Rows are removed in place; the removed ids are printed. Run after each research wave:
uv run scripts/prune_weak_not_found.py <city> [<city> ...]
"""

import csv
import sys

from common import ROOT, read

WEAK = ("meetup", "eventbrite", "coursehorse", "weak evidence")


def weak(note):
    n = note.lower()
    return any(w in n for w in WEAK) and "searched" not in n


def main():
    for cid in sys.argv[1:] or [
        p.name for p in sorted((ROOT / "data/cities").iterdir()) if p.is_dir()
    ]:
        d = ROOT / "data/cities" / cid / "not_found"
        removed = []
        for p in sorted(d.glob("*.csv")):
            rows = read(p)
            keep = [r for r in rows if not weak(r.get("note", ""))]
            removed += [r["id"] for r in rows if weak(r.get("note", ""))]
            if len(keep) != len(rows):
                with open(p, "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=["id", "note"])
                    w.writeheader()
                    w.writerows(keep)
        if removed:
            print(f"{cid}: pruned {len(removed)} weak not_found: {' '.join(removed)}")


if __name__ == "__main__":
    main()
