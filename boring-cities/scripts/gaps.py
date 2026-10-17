"""What is still unresolved? An activity is resolved for a city once it has a research row or a
"searched, nothing found" note.

  uv run scripts/gaps.py <city> [--all] [--priority]   unresolved activities for one city, as CSV on stdout
  uv run scripts/gaps.py --waves                       cities ranked by how many activities are unresolved

By default activities that data/osm_tags.json can cover are left out; pass --all to include them. With
--priority the rows are ordered by how many other cities already have them (descending), so filling the top
rows grows the set of activities researched in every city, which is what the comparison uses.
"""

import csv
import json
import sys

from common import DATA, city_arg, read, table


def resolved_by_city():
    ids = {}
    for name in ("research", "not_found"):
        for r in table(name):
            ids.setdefault(r["city"], set()).add(r["id"])
    return ids


def main():
    universe = read(DATA / "universe.csv")
    ids = resolved_by_city()
    if "--waves" in sys.argv:
        every = {u["id"] for u in universe}
        rows = sorted(
            (
                (len(every - ids.get(c["id"], set())), c["id"])
                for c in read(DATA / "cities.csv")
            ),
            reverse=True,
        )
        for unresolved, cid in rows:
            print(
                f"{cid:<14} resolved {len(every) - unresolved:>3}  unresolved {unresolved:>3}"
            )
        return
    city = city_arg()
    done = set(ids.get(city["id"], set()))
    if "--all" not in sys.argv:
        done |= set(json.load(open(DATA / "osm_tags.json")))
    gaps = [u for u in universe if u["id"] not in done]
    if "--priority" in sys.argv:
        researched = {}
        for r in table("research"):
            researched.setdefault(r["city"], set()).add(r["id"])
        others = [s for c, s in researched.items() if c != city["id"]]
        gaps.sort(key=lambda u: -sum(u["id"] in o for o in others))
    w = csv.DictWriter(
        sys.stdout,
        fieldnames=["id", "activity", "category", "subcategory", "seed_source"],
    )
    w.writeheader()
    w.writerows(gaps)
    print(f"{city['name']}: {len(gaps)} unresolved of {len(universe)}", file=sys.stderr)


if __name__ == "__main__":
    main()
