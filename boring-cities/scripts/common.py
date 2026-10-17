"""Shared helpers: paths, and access to the shared data tables.

Everything lives in a few CSVs under data/. Tables that vary by city (research, not_found, curation,
geocode, url_check, osm_venues, osm_counts) carry a `city` column first; research and not_found also
carry a `batch` column naming the research round a row came from.
"""

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = (
    ROOT.parent / "assets" / "boring-cities"
)  # the explorer (app.js, data.json, ...), served by the blog


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def cities():
    """All cities from data/cities.csv (values are strings)."""
    return read(DATA / "cities.csv")


def city_arg():
    """The city dict for the id on the command line (default singapore), with numeric lat/lon/radius_km."""
    cid = sys.argv[1] if len(sys.argv) > 1 else "singapore"
    by_id = {c["id"]: c for c in cities()}
    if cid not in by_id:
        sys.exit(f"unknown city {cid!r}; choose from {', '.join(by_id)}")
    c = by_id[cid]
    c["lat"], c["lon"], c["radius_km"] = (
        float(c["lat"]),
        float(c["lon"]),
        float(c["radius_km"]),
    )
    return c


def table(name):
    """Every row of data/<name>.csv (each row has a `city` key); empty if the table doesn't exist yet."""
    path = DATA / f"{name}.csv"
    return read(path) if path.exists() else []


def city_rows(name, city_id):
    """The rows of table `name` for one city, without the `city` column."""
    return [
        {k: v for k, v in r.items() if k != "city"}
        for r in table(name)
        if r["city"] == city_id
    ]


def save_city_rows(name, city_id, rows, fields):
    """Replace one city's rows in data/<name>.csv, leaving every other city's rows as they were."""
    order = [c["id"] for c in cities()]
    by_city = {}
    for r in table(name):
        by_city.setdefault(r["city"], []).append(r)
    by_city[city_id] = [
        {"city": city_id, **{f: r.get(f, "") for f in fields}} for r in rows
    ]
    ordered = sorted(
        by_city, key=lambda c: order.index(c) if c in order else len(order)
    )
    with open(DATA / f"{name}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["city", *fields])
        w.writeheader()
        for c in ordered:
            w.writerows(by_city[c])


def city_activities(city_id):
    """One city's built rows (from the explorer's long-format activities.csv; run build.py first)."""
    path = SITE / "activities.csv"
    if not path.exists():
        sys.exit("run `uv run boring-cities/scripts/build.py` first")
    return [
        {k: v for k, v in r.items() if k != "city"}
        for r in read(path)
        if r["city"] == city_id
    ]


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return 12742 * math.asin(math.sqrt(a))
