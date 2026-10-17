"""Reports on the built data (run build.py first).

uv run scripts/report.py coverage            researched counts per city, overlaps, confidence, completeness
uv run scripts/report.py compare [city ...]  cross-city stats on activities researched in every chosen city
uv run scripts/report.py numbers [N]         the figures the blog post quotes (N best-covered cities, default 10)
uv run scripts/report.py review <city>       dead source links and weak geocode matches for one city
"""

import itertools
import json
import re
import sys
from collections import Counter

from common import SITE, city_activities, city_arg, city_rows


def load():
    return json.load(open(SITE / "data.json"))


def pct(a, b):
    return f"{round(100 * a / b)}%" if b else "-"


def coverage():
    d = load()
    cities, n = d["cities"], len(d["universe"])
    sets = {c["name"]: set(c["rows"]) for c in cities}
    for c in cities:
        k = Counter(r["doable"] for r in c["rows"].values())
        print(f"{c['name']:<14} {len(c['rows']):>3}/{n}  {dict(k)}")
    print("in all cities:", len(set.intersection(*sets.values())))
    for (a, sa), (b, sb) in itertools.combinations(sets.items(), 2):
        print(f"  {a} & {b}: {len(sa & sb)}")
    print("\nconfidence / verification per city:")
    for c in cities:
        rows = c["rows"].values()
        low = sum(r["confidence"] == "low" for r in rows)
        ver = sum(r["verified"] for r in rows)
        print(
            f"  {c['name']:<14} low-confidence {100 * low / len(rows):.0f}%   verified {100 * ver / len(rows):.0f}%"
        )
    print(
        "\nresearch completeness (researched / searched-without-evidence / not yet searched):"
    )
    for c in cities:
        nf = len(c.get("notFound", []))
        print(
            f"  {c['name']:<14} {len(c['rows']):>3} / {nf:>3} / {n - len(c['rows']) - nf:>3}"
        )


def compare(ids):
    d = load()
    cities = [
        c for c in d["cities"] if c["id"] in (ids or [c["id"] for c in d["cities"]])
    ]
    common = [u for u in d["universe"] if all(u["id"] in c["rows"] for c in cities)]
    print(
        f"{len(common)} activities researched in all of: {', '.join(c['name'] for c in cities)}\n"
    )
    print(
        f"{'city':<14} {'yes':>5} {'yes+partial':>12} {'cheap&close':>12} {'beginner':>9} {'free/$':>7}"
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
            f"{c['name']:<14} {pct(len(yes), len(rows)):>5} {pct(len(ok), len(rows)):>12} {pct(len(cc), len(ok)):>12} "
            f"{pct(len(beg), len(ok)):>9} {pct(len(cheap), len(ok)):>7}"
        )
    print("\nBy category (share fully doable):")
    print(f"{'':<26}" + "".join(f"{c['name']:>14}" for c in cities))
    for cat in sorted({u["category"] for u in common}):
        items = [u for u in common if u["category"] == cat]
        cells = [
            pct(Counter(c["rows"][u["id"]]["doable"] for u in items)["yes"], len(items))
            for c in cities
        ]
        print(f"{cat + f' ({len(items)})':<26}" + "".join(f"{x:>14}" for x in cells))
    print("\nActivities where cities differ (doable = yes):")
    for u in common:
        marks = [c["rows"][u["id"]]["doable"] == "yes" for c in cities]
        if any(marks) and not all(marks):
            have = [c["name"] for c, m in zip(cities, marks) if m]
            lack = [c["name"] for c, m in zip(cities, marks) if not m]
            print(f"  {u['activity']}: has {', '.join(have)}; lacks {', '.join(lack)}")


def numbers(top_n):
    d = load()
    cities = sorted(d["cities"], key=lambda c: -len(c["rows"]))
    print(
        f"Coverage (researched / {len(d['universe'])}):",
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
        f"Rows passing the stricter check: {min(ver.values()):.0f}% ({min(ver, key=ver.get)}) to {max(ver.values()):.0f}% ({max(ver, key=ver.get)})"
    )
    top = cities[:top_n]
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
    print("\nBy category (share fully doable), min-max across these cities:")
    for cat in sorted({u["category"] for u in common}):
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


STOP = {
    "the",
    "of",
    "and",
    "club",
    "centre",
    "center",
    "city",
    "association",
    "society",
    "school",
    "studio",
    "at",
    "for",
    "in",
}


def words(s):
    return {
        w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP
    }


def review():
    city = city_arg()
    keep = {r["id"] for r in city_activities(city["id"])}
    bad = [
        r
        for r in city_rows("url_check", city["id"])
        if r["id"] in keep
        and not r["status"].startswith("2")
        and r["status"] != "blocked"
    ]
    print(f"{len(bad)} dead urls in kept rows")
    for r in bad:
        print(" ", r["status"], r["id"], r["url"][:100])
    print("weak geocode matches (name overlap < 60%):")
    for r in city_rows("geocode", city["id"]):
        if not r["lat"]:
            continue
        v, m = words(r["venue"].split("(")[0]), words(r["matched_name"])
        frac = len(v & m) / max(1, len(v))
        if frac < 0.6:
            print(f"  {frac:.2f} {r['id']}: {r['venue']!r} -> {r['matched_name']!r}")


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if cmd == "coverage":
        coverage()
    elif cmd == "compare":
        compare(args)
    elif cmd == "numbers":
        numbers(int(args[0]) if args else 10)
    elif cmd == "review":
        sys.argv = [sys.argv[0], *args]  # city_arg() reads the city id from argv[1]
        review()
    else:
        sys.exit(__doc__)
