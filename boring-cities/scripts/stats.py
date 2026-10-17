"""Print headline statistics from data/activities.csv (used to write the blog post)."""

import csv
from collections import Counter

from common import city_arg

_, _CDIR = city_arg()
rows = list(csv.DictReader(open(_CDIR / "activities.csv", newline="")))
n = len(rows)
doable = [r for r in rows if r["doable"] in ("yes", "partial")]
print("total", n, Counter(r["doable"] for r in rows))
print("verified-ish (conf!=low):", sum(r["confidence"] != "low" for r in rows))
print("seed:", Counter(r["seed_source"].split(":")[0] for r in rows))
print("\nby category (yes+partial / n):")
cats = Counter(r["category"] for r in rows)
for c, k in cats.most_common():
    d = sum(1 for r in rows if r["category"] == c and r["doable"] != "no")
    print(f"  {c}: {d}/{k}")
print("\ndoable cost:", Counter(r["cost_tier"] for r in doable))
print("doable distance:", Counter(r["distance_tier"] for r in doable))
cheap_close = sum(
    1
    for r in doable
    if r["cost_tier"] in ("free", "$", "$$")
    and r["distance_tier"] in ("central", "near")
)
print("cheap(<=$$) & central/near:", cheap_close, "of", len(doable))
free_or_cheap = sum(1 for r in doable if r["cost_tier"] in ("free", "$"))
print("free or $:", free_or_cheap)
print(
    "beginner friendly:",
    sum(r["beginner_friendly"] == "y" for r in doable),
    "of",
    len(doable),
)
print("equipment:", Counter(r["equipment"] for r in doable))
print("\npartial:", [r["activity"] for r in rows if r["doable"] == "partial"])
print("\nno:", [r["activity"] for r in rows if r["doable"] == "no"])

print("\nseed split (yes / partial / no):")
for src in ("wikipedia", "brainstorm"):
    sub = [r for r in rows if r["seed_source"].startswith(src)]
    c = Counter(r["doable"] for r in sub)
    print(
        f"  {src}: n={len(sub)} yes={c['yes']} ({100 * c['yes'] / len(sub):.0f}%) partial={c['partial']} no={c['no']}"
    )
