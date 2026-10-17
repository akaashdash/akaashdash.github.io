"""List yes/partial rows whose coordinates are beyond the 30 km metro definition (candidates to drop).

Uses each city's activities.csv (coordinates from the agent or geocode.csv). Rows without coordinates are
not checked. Run after build + geocode: uv run scripts/far_rows.py [city ...]
"""

import sys

from common import ROOT, km, read

LIMIT_KM = 33  # 30 km definition plus a little slack for geocoding of large venues

cities = {c["id"]: c for c in read(ROOT / "data/cities.csv")}
for cid in sys.argv[1:] or list(cities):
    c = cities[cid]
    path = ROOT / "data/cities" / cid / "activities.csv"
    if not path.exists():
        continue
    far = []
    for r in read(path):
        if r["doable"] == "no" or not r["lat"]:
            continue
        d = km(float(r["lat"]), float(r["lon"]), float(c["lat"]), float(c["lon"]))
        if d > LIMIT_KM:
            far.append((d, r["id"], r["venue"][:40]))
    if far:
        print(f"{c['name']}: {len(far)} beyond {LIMIT_KM} km")
        for d, i, v in sorted(far, reverse=True):
            print(f"  {d:5.0f} km  {i}: {v}")
