"""Pull venue points for one city from OpenStreetMap (Overpass) within radius_km of its centre.

Writes data/cities/<city>/venues.csv (group, kind, name, lat, lon; at most MAX_POINTS per group,
evenly sampled) and venue_counts.csv (the true count per group, for cross-city comparison).
Run: uv run scripts/fetch_osm.py <city>
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request

from common import city_arg

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
MAX_POINTS = 6000
GROUPS = {
    "Sports facility": [
        'nwr["leisure"~"^(sports_centre|swimming_pool|fitness_centre|stadium|golf_course|track|ice_rink)$"]',
        'nwr["sport"]["name"]["leisure"!="pitch"]',
    ],
    "Park & nature": [
        'nwr["leisure"~"^(park|nature_reserve|garden)$"]["name"]',
        'nwr["boundary"="protected_area"]["name"]',
    ],
    "Water & marina": [
        'nwr["leisure"~"^(marina|slipway|water_park)$"]',
        'nwr["sport"~"sail|canoe|kayak|diving|surf|rowing"]',
    ],
    "Arts & culture": [
        'nwr["amenity"~"^(arts_centre|theatre|cinema|library|community_centre|studio|music_school)$"]',
        'nwr["tourism"~"^(museum|gallery)$"]',
    ],
    "Craft & maker": [
        'nwr["craft"]',
        'nwr["shop"~"^(art|craft|musical_instrument|hobby|games|model)$"]',
    ],
    "Learning": [
        'nwr["amenity"~"^(language_school|dancing_school|driving_school|training)$"]'
    ],
    "Food & drink": [
        'nwr["amenity"~"^(food_court|marketplace)$"]["name"]',
        'nwr["craft"~"brewery|winery|distillery"]',
    ],
}


def run(query):
    data = urllib.parse.urlencode({"data": query}).encode()
    for ep in ENDPOINTS:
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    ep,
                    data=data,
                    headers={"User-Agent": "boring-cities/0.1 (research)"},
                )
                return json.load(urllib.request.urlopen(req, timeout=240))
            except Exception as e:  # noqa: BLE001
                print("retry", ep, e, flush=True)
                time.sleep(15 * (attempt + 1))
    raise RuntimeError("overpass failed")


def main():
    if (
        len(sys.argv) < 2
    ):  # never default to a city: a stray argument-less run must not overwrite data
        sys.exit("usage: uv run scripts/fetch_osm.py <city> [group ...]")
    city, cdir = city_arg()
    around = f"(around:{int(city['radius_km'] * 1000)},{city['lat']},{city['lon']})"
    rows, counts = [], []
    only = sys.argv[
        2:
    ]  # optional: refetch just these groups and merge into the existing files
    for group, filters in GROUPS.items():
        if only and group not in only:
            continue
        body = "".join(f"{f}{around};" for f in filters)
        try:
            # true count first (cheap), then a capped sample of points for the map
            total = int(
                run(f"[out:json][timeout:200];({body});out count;")["elements"][0][
                    "tags"
                ]["total"]
            )
            res = run(f"[out:json][timeout:200];({body});out center tags {MAX_POINTS};")
        except RuntimeError:
            print(group, "FAILED, skipped", flush=True)
            continue
        pts = []
        for el in res["elements"]:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None:
                continue
            t = el["tags"]
            kind = next(
                (
                    t[k]
                    for k in (
                        "leisure",
                        "amenity",
                        "tourism",
                        "craft",
                        "shop",
                        "sport",
                        "boundary",
                    )
                    if k in t
                ),
                "",
            )
            pts.append((group, kind, t.get("name", ""), round(lat, 5), round(lon, 5)))
        counts.append((group, total))
        rows += pts
        print(group, total, f"({len(pts)} points)", flush=True)
        time.sleep(5)
    cdir.mkdir(parents=True, exist_ok=True)
    if only and (cdir / "venues.csv").exists():
        with open(cdir / "venues.csv", newline="") as f:
            keep = [
                r for r in csv.reader(f) if r and r[0] != "group" and r[0] not in only
            ]
        rows = [tuple(r[:3]) + (float(r[3]), float(r[4])) for r in keep] + rows
        with open(cdir / "venue_counts.csv", newline="") as f:
            counts = [
                (g, int(c)) for g, c in list(csv.reader(f))[1:] if g not in only
            ] + counts
    with open(cdir / "venues.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "kind", "name", "lat", "lon"])
        w.writerows(rows)
    with open(cdir / "venue_counts.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "count"])
        w.writerows(counts)
    print(len(rows), "points written;", sum(c for _, c in counts), "venues counted")


if __name__ == "__main__":
    main()
