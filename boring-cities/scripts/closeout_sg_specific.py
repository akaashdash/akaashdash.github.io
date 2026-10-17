"""Record Singapore-specific activities as 'searched, not applicable' in cities that lack a result.

These (Malay dance, Peranakan beadwork, ...) are specific to Singapore culture, so a missing
row elsewhere is a scope note rather than a research gap. Writes not_found/closeout.csv.
Run: uv run scripts/closeout_sg_specific.py
"""

import csv

from common import ROOT, read

SG_SPECIFIC = {
    "malay-dance": "specific to Malay/Singapore culture; not searched here",
    "peranakan-beadwork": "specific to Peranakan/Singapore culture; not searched here",
}

for city in read(ROOT / "data/cities.csv"):
    cid = city["id"]
    if cid == "singapore":
        continue
    base = ROOT / "data/cities" / cid
    done = set()
    for f in (base / "research").glob("*.csv"):
        done |= {r["id"] for r in read(f)}
    for f in (base / "not_found").glob("*.csv"):
        done |= {r["id"] for r in read(f)}
    target = base / "not_found/closeout.csv"
    rows = read(target) if target.exists() else []
    have = {r["id"] for r in rows}
    add = [
        {"id": i, "note": n}
        for i, n in SG_SPECIFIC.items()
        if i not in done and i not in have
    ]
    if add:
        with open(target, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["id", "note"])
            w.writeheader()
            w.writerows(rows + add)
        print(f"{cid}: +{len(add)}")
