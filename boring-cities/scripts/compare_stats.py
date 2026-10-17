"""Cross-city statistics on the activities researched in every chosen city (default: all cities).

Run: uv run scripts/compare_stats.py [city-id ...]
"""

import json
import sys
from collections import Counter

from common import SITE

d = json.load(open(SITE / "data.json"))
chosen = sys.argv[1:] or [c["id"] for c in d["cities"]]
cities = [c for c in d["cities"] if c["id"] in chosen]
common = [u for u in d["universe"] if all(u["id"] in c["rows"] for c in cities)]
print(
    f"{len(common)} activities researched in all of: {', '.join(c['name'] for c in cities)}\n"
)


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "-"


print(
    f"{'city':<10} {'yes':>5} {'yes+partial':>12} {'cheap&close':>12} {'beginner':>9} {'free/$':>7}"
)
for c in cities:
    rows = [c["rows"][u["id"]] for u in common]
    ok = [r for r in rows if r["doable"] != "no"]
    yes = [r for r in rows if r["doable"] == "yes"]
    cc = [
        r
        for r in ok
        if r["distance_tier"] in ("central", "near")
        and r["cost_tier"] in ("free", "$", "$$")
    ]
    beg = [r for r in ok if r["beginner_friendly"] == "y"]
    cheap = [r for r in ok if r["cost_tier"] in ("free", "$")]
    print(
        f"{c['name']:<10} {pct(len(yes), len(rows)):>5} {pct(len(ok), len(rows)):>12} {pct(len(cc), len(ok)):>12} {pct(len(beg), len(ok)):>9} {pct(len(cheap), len(ok)):>7}"
    )

print("\nBy category (share fully doable):")
cats = sorted({u["category"] for u in common})
print(f"{'':<26}" + "".join(f"{c['name']:>10}" for c in cities))
for cat in cats:
    items = [u for u in common if u["category"] == cat]
    cells = []
    for c in cities:
        k = Counter(c["rows"][u["id"]]["doable"] for u in items)
        cells.append(pct(k["yes"], len(items)))
    print(f"{cat + f' ({len(items)})':<26}" + "".join(f"{x:>10}" for x in cells))

print("\nActivities where cities differ (doable = yes):")
for u in common:
    marks = [c["rows"][u["id"]]["doable"] == "yes" for c in cities]
    if any(marks) and not all(marks):
        have = [c["name"] for c, m in zip(cities, marks) if m]
        lack = [c["name"] for c, m in zip(cities, marks) if not m]
        print(f"  {u['activity']}: has {', '.join(have)}; lacks {', '.join(lack)}")
