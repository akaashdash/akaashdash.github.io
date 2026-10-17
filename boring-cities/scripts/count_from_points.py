"""Derive venue_counts.csv for a city from its (complete, unsampled) venues.csv, within radius_km.

Fallback for when the Overpass count queries are too slow. Only valid when venues.csv holds every
point (not a sample), as Singapore's first fetch did. Note that fetch predates the 'pitch' exclusion
in fetch_osm.py, so its sports-facility count is somewhat higher than a fresh fetch would give.
Run: uv run scripts/count_from_points.py <city>
"""

import csv
from collections import Counter

from common import city_arg, km, read

city, cdir = city_arg()
counts = Counter()
for r in read(cdir / "venues.csv"):
    if (
        km(float(r["lat"]), float(r["lon"]), city["lat"], city["lon"])
        <= city["radius_km"]
    ):
        counts[r["group"]] += 1
with open(cdir / "venue_counts.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["group", "count"])
    w.writerows(sorted(counts.items()))
print(dict(counts))
