"""Shared helpers for the per-city scripts."""

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT.parent / "assets" / "boring-cities"  # the explorer (index.html, app.js, data.json, ...), served by the blog


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def city_arg():
    """Return (city dict, city directory) for the city id on the command line (default singapore)."""
    cid = sys.argv[1] if len(sys.argv) > 1 else "singapore"
    cities = {c["id"]: c for c in read(ROOT / "data/cities.csv")}
    if cid not in cities:
        sys.exit(f"unknown city {cid!r}; choose from {', '.join(cities)}")
    c = cities[cid]
    c["lat"], c["lon"], c["radius_km"] = (
        float(c["lat"]),
        float(c["lon"]),
        float(c["radius_km"]),
    )
    return c, ROOT / "data/cities" / cid


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return 12742 * math.asin(math.sqrt(a))
