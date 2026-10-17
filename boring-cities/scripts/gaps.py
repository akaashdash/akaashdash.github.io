"""List universe activities with no research row yet for one city -> data/cities/<city>/gaps.csv.

Rows already in research/*.csv count as done (even if later curated away). By default activities that
scripts/osm_evidence.py can cover (data/osm_tags.json) are left out so search-based agents don't
duplicate that work; pass --all to include them. With --priority the rows are ordered by how many
other cities already have them (descending), so filling the top rows grows the set of activities
researched in every city, which is what the comparison uses. Gap-fill agents read gaps.csv and write
data/cities/<city>/research/gaps-<n>.csv.
Run: uv run scripts/gaps.py <city> [--all] [--priority]
"""

import csv
import json
import sys

from common import ROOT, city_arg, read


def researched_ids(cdir):
    ids = set()
    for p in sorted((cdir / "research").glob("*.csv")):
        ids |= {r["id"] for r in read(p)}
    return ids


def main():
    city, cdir = city_arg()
    done = researched_ids(cdir)
    for p in sorted(
        (cdir / "not_found").glob("*.csv")
    ):  # searched, nothing found: don't redo
        done |= {r["id"] for r in read(p)}
    if "--all" not in sys.argv:
        done |= set(json.load(open(ROOT / "data/osm_tags.json")))
    universe = read(ROOT / "data/universe.csv")
    gaps = [u for u in universe if u["id"] not in done]
    if "--priority" in sys.argv:
        others = [
            researched_ids(d)
            for d in (ROOT / "data/cities").iterdir()
            if d.is_dir() and d != cdir and (d / "research").exists()
        ]
        gaps.sort(key=lambda u: -sum(u["id"] in o for o in others))
    with open(cdir / "gaps.csv", "w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["id", "activity", "category", "subcategory", "seed_source"]
        )
        w.writeheader()
        w.writerows(gaps)
    print(f"{city['name']}: {len(gaps)} gaps of {len(universe)}")


if __name__ == "__main__":
    main()
