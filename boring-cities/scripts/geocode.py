"""Geocode venue names for one city via OSM Nominatim -> data/geocode.csv (rows for that city).

A hit is accepted only if it lies near the city centre AND its (English) name shares a significant
word with the venue string. Misses are recorded so reruns are cheap. build.py uses accepted
coordinates for rows whose own lat/lon is blank. Nominatim policy: max 1 request/second.
Run: uv run scripts/geocode.py <city>
"""

import json
import re
import time
import urllib.parse
import urllib.request

from common import city_activities, city_arg, city_rows, km, save_city_rows

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
FIELDS = ["id", "venue", "lat", "lon", "matched_name"]


def words(s):
    return {
        w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP
    }


def query_variants(venue):
    first = re.split(r"\s*(?:/|;|\()\s*", venue)[0].strip()
    return [x for x in dict.fromkeys([venue, first]) if x]


def lookup(q, city):
    dlat = city["radius_km"] / 111
    dlon = dlat / max(0.2, abs(__import__("math").cos(city["lat"] * 3.14159 / 180)))
    params = {
        "q": f"{q}, {city['name']}",
        "format": "json",
        "limit": 3,
        "countrycodes": city["cc"],
        "accept-language": "en",
        "viewbox": f"{city['lon'] - dlon},{city['lat'] + dlat},{city['lon'] + dlon},{city['lat'] - dlat}",
        "bounded": 1,
    }
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params),
        headers={"User-Agent": "boring-cities/0.1 (personal blog research)"},
    )
    return json.load(urllib.request.urlopen(req, timeout=30))


def main():
    city = city_arg()
    done = {r["id"]: r for r in city_rows("geocode", city["id"])}
    rows = [r for r in city_activities(city["id"]) if r["venue"] and not r["lat"]]
    for r in rows:
        if r["id"] in done and done[r["id"]]["venue"] == r["venue"]:
            continue
        hit = None
        for q in query_variants(r["venue"]):
            time.sleep(1.1)
            try:
                res = lookup(q, city)
            except Exception as e:  # noqa: BLE001
                print("err", r["id"], e, flush=True)
                continue
            for h in res:
                lat, lon = float(h["lat"]), float(h["lon"])
                if km(lat, lon, city["lat"], city["lon"]) > city["radius_km"] * 1.6:
                    continue
                skip = set(re.findall(r"[a-z0-9]+", city["name"].lower()))
                want = words(q) - skip
                got = words(h.get("name") or h["display_name"].split(",")[0])
                if want and len(want & got) / len(want) >= 0.6:
                    hit = (lat, lon, h.get("name") or h["display_name"].split(",")[0])
                    break
            if hit:
                break
        done[r["id"]] = {
            "id": r["id"],
            "venue": r["venue"],
            "lat": f"{hit[0]:.5f}" if hit else "",
            "lon": f"{hit[1]:.5f}" if hit else "",
            "matched_name": hit[2] if hit else "",
        }
        print(
            ("ok  " if hit else "miss"),
            r["id"],
            "->",
            hit[2] if hit else "",
            flush=True,
        )
        save_city_rows("geocode", city["id"], list(done.values()), FIELDS)


if __name__ == "__main__":
    main()
