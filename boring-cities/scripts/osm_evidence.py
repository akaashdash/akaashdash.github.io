"""Fill research gaps for one city from OpenStreetMap tags (no search budget needed).

For each universe activity that has no research row yet and appears in data/osm_tags.json, query
Overpass within MAX_KM of the city centre. If a *named* venue with the matching tag exists, write a
`yes` row (confidence medium: tagged in OSM, not verified as currently operating) citing the OSM
element. No hits writes nothing: absence in OSM is never evidence of "no".
Output: data/cities/<city>/research/osm.csv (rebuilt each run). Run: uv run scripts/osm_evidence.py <city>
"""

import csv
import json
import time
import urllib.parse
import urllib.request

from common import ROOT, city_arg, km, read

MAX_KM = 20
COLUMNS = (
    "id activity category subcategory seed_source doable how venue area lat lon "
    "distance_tier cost_tier beginner_friendly equipment source_url confidence"
).split()
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


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
                return json.load(urllib.request.urlopen(req, timeout=120))
            except Exception as e:  # noqa: BLE001
                print("  retry", e, flush=True)
                time.sleep(10 * (attempt + 1))
    return None


def label(t):
    return t.get("name:en") or t.get("name") or ""


def main():
    city, cdir = city_arg()
    tags = json.load(open(ROOT / "data/osm_tags.json"))
    done = set()
    for p in sorted((cdir / "research").glob("*.csv")):
        if p.name != "osm.csv":
            done |= {r["id"] for r in read(p)}
    universe = {u["id"]: u for u in read(ROOT / "data/universe.csv")}
    around = f"(around:{MAX_KM * 1000},{city['lat']},{city['lon']})"
    out, n_query = [], 0
    for aid, filters in tags.items():
        if aid in done or aid not in universe:
            continue
        body = "".join(f"{f}{around};" for f in filters)
        res = run(f"[out:json][timeout:60];({body});out center tags 100;")
        n_query += 1
        time.sleep(2)
        if not res:
            continue
        hits = []
        for el in res["elements"]:
            t = el.get("tags", {})
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if lat is None or not label(t):
                continue
            hits.append(
                (
                    km(lat, lon, city["lat"], city["lon"]),
                    label(t),
                    lat,
                    lon,
                    el["type"],
                    el["id"],
                    t,
                )
            )
        if not hits:
            print(f"  none  {aid}", flush=True)
            continue
        hits.sort()
        d, name, lat, lon, typ, eid, t = hits[0]
        u = universe[aid]
        area = (
            t.get("addr:suburb")
            or t.get("addr:city_district")
            or t.get("addr:neighbourhood")
            or t.get("addr:district")
            or ""
        )
        out.append(
            {
                **u,
                "doable": "yes",
                "how": f"Listed in OpenStreetMap: {name} (nearest of {len(hits)} tagged venues within {MAX_KM} km); not checked for current opening.",
                "venue": name,
                "area": area,
                "lat": f"{lat:.5f}",
                "lon": f"{lon:.5f}",
                "distance_tier": "",
                "cost_tier": "",
                "beginner_friendly": "",
                "equipment": "",
                "source_url": f"https://www.openstreetmap.org/{typ}/{eid}",
                "confidence": "medium",
            }
        )
        print(f"  yes   {aid}: {name} ({d:.1f} km, {len(hits)} hits)", flush=True)
        with open(cdir / "research/osm.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(out)
    with open(cdir / "research/osm.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    print(f"{city['name']}: {len(out)} OSM-evidenced rows from {n_query} queries")


if __name__ == "__main__":
    main()
