"""Print the figures the blog post quotes, straight from site/data.json.

Compares the N best-covered cities (default 8) on the activities researched in all of them.
Run after build.py: uv run scripts/post_numbers.py [N]
"""

import json
import sys
from collections import Counter

from common import SITE

d = json.load(open(SITE / "data.json"))
n_all = len(d["universe"])
cities = sorted(d["cities"], key=lambda c: -len(c["rows"]))
print(
    "Coverage (researched / 299):",
    ", ".join(f"{c['name']} {len(c['rows'])}" for c in cities),
)
low = {
    c["name"]: 100
    * sum(r["confidence"] == "low" for r in c["rows"].values())
    / len(c["rows"])
    for c in cities
}
ver = {
    c["name"]: 100 * sum(r["verified"] for r in c["rows"].values()) / len(c["rows"])
    for c in cities
}
print(
    f"Low-confidence share: {min(low.values()):.0f}% ({min(low, key=low.get)}) to {max(low.values()):.0f}% ({max(low, key=low.get)})"
)
print(
    f"Strict-mode keeps: {min(ver.values()):.0f}% ({min(ver, key=ver.get)}) to {max(ver.values()):.0f}% ({max(ver, key=ver.get)})"
)

top = cities[: int(sys.argv[1]) if len(sys.argv) > 1 else 8]
common = [u for u in d["universe"] if all(u["id"] in c["rows"] for c in top)]
print(
    f"\n{len(common)} activities researched in all of: {', '.join(c['name'] for c in top)}\n"
)
print("| | fully doable | at least partly | within 15 km and under ~US$45 |")
print("|---|---|---|---|")
for c in top:
    rows = [c["rows"][u["id"]] for u in common]
    ok = [r for r in rows if r["doable"] != "no"]
    yes = [r for r in rows if r["doable"] == "yes"]
    cc = [
        r
        for r in ok
        if r["distance_tier"] in ("central", "near")
        and r["cost_tier"] in ("free", "$", "$$")
    ]
    print(
        f"| {c['name']} | {round(100 * len(yes) / len(rows))}% | {round(100 * len(ok) / len(rows))}% | {round(100 * len(cc) / max(1, len(ok)))}% |"
    )

cats = sorted({u["category"] for u in common})
print("\nBy category (share fully doable), min-max across these cities:")
for cat in cats:
    items = [u for u in common if u["category"] == cat]
    vals = [
        100 * sum(c["rows"][u["id"]]["doable"] == "yes" for u in items) / len(items)
        for c in top
    ]
    print(f"  {cat} ({len(items)}): {min(vals):.0f}-{max(vals):.0f}%")
diff = [
    u
    for u in common
    if 0 < sum(c["rows"][u["id"]]["doable"] == "yes" for c in top) < len(top)
]
print(
    f"\nActivities that differ somewhere: {len(diff)} of {len(common)} ({round(100 * len(diff) / len(common))}%)"
)
geo = Counter()
for u in common:
    has = [c["name"] for c in top if c["rows"][u["id"]]["doable"] == "yes"]
    if 0 < len(has) < len(top) and u["category"] in (
        "Extreme & Exotic",
        "Water & Air",
        "Outdoors & Nature",
    ):
        geo[u["activity"]] = ", ".join(has)
print("Geography-flavoured differences:", dict(geo))
