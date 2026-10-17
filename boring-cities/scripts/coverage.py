"""Coverage report: researched activities per city and overlap between cities (from site/data.json)."""

import itertools
import json
from collections import Counter

from common import SITE

d = json.load(open(SITE / "data.json"))
cities = d["cities"]
n = len(d["universe"])
sets = {c["name"]: set(c["rows"]) for c in cities}
for c in cities:
    k = Counter(r["doable"] for r in c["rows"].values())
    print(f"{c['name']:<10} {len(c['rows']):>3}/{n}  {dict(k)}")
print("in all cities:", len(set.intersection(*sets.values())))
for (a, sa), (b, sb) in itertools.combinations(sets.items(), 2):
    print(f"  {a} & {b}: {len(sa & sb)}")

print("\nconfidence / verification per city:")
for c in cities:
    rows = c["rows"].values()
    low = sum(r["confidence"] == "low" for r in rows)
    ver = sum(r["verified"] for r in rows)
    print(
        f"  {c['name']:<10} low-confidence {100 * low / len(rows):.0f}%   verified {100 * ver / len(rows):.0f}%"
    )

print(
    "\nresearch completeness (researched / searched-without-evidence / not yet searched):"
)
for c in cities:
    nf = len(c.get("notFound", []))
    print(
        f"  {c['name']:<10} {len(c['rows']):>3} / {nf:>3} / {n - len(c['rows']) - nf:>3}"
    )
