"""Rank cities by unresolved activities (not researched and not in not_found), most unresolved first.

The first three lines are the next research wave; `gaps.py <city> --all --priority` then writes each
city's gap list. Run: uv run scripts/next_wave.py
"""

from common import ROOT, read

universe = {u["id"] for u in read(ROOT / "data/universe.csv")}
rows = []
for c in read(ROOT / "data/cities.csv"):
    cdir = ROOT / "data/cities" / c["id"]
    ids = set()
    for sub in ("research", "not_found"):
        for p in (cdir / sub).glob("*.csv"):
            ids |= {r["id"] for r in read(p)}
    resolved = len(ids & universe)
    rows.append((len(universe) - resolved, c["id"], resolved))
for unresolved, cid, resolved in sorted(rows, reverse=True):
    print(f"{cid:<14} resolved {resolved:>3}  unresolved {unresolved:>3}")
