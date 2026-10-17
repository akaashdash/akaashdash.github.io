"""Add one research round's output to the shared tables.

  uv run scripts/add_batch.py <city> <batch> <rows.csv>                 17-column research rows -> data/research.csv
  uv run scripts/add_batch.py <city> <batch> <notfound.csv> --not-found   id,note rows         -> data/not_found.csv

<batch> is a short label for the round (for example w5, f2, r1) and is stored with every row, so you can
always tell which round a row came from. Then run build.py. A batch label can only be used once per city.
"""

import csv
import sys

from common import DATA, city_arg, table

RESEARCH = (
    "id activity category subcategory seed_source doable how venue area lat lon "
    "distance_tier cost_tier beginner_friendly equipment source_url confidence"
).split()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    city = city_arg()  # reads the city id from argv[1]
    _, batch, path = args
    name, fields = (
        ("not_found", ["id", "note"])
        if "--not-found" in sys.argv
        else ("research", RESEARCH)
    )
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != fields:
            sys.exit(f"{path}: expected columns {fields}, got {reader.fieldnames}")
        rows = list(reader)
    if any(r["city"] == city["id"] and r["batch"] == batch for r in table(name)):
        sys.exit(f"batch {batch!r} already exists for {city['id']} in {name}.csv")
    target = DATA / f"{name}.csv"
    fresh = not target.exists()
    with open(target, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["city", "batch", *fields])
        if fresh:
            w.writeheader()
        w.writerows({"city": city["id"], "batch": batch, **r} for r in rows)
    print(f"added {len(rows)} rows to {name}.csv ({city['id']}, batch {batch})")


if __name__ == "__main__":
    main()
