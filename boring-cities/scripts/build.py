"""Build every city: data/research.csv (+ curation, geocode, url_check) -> assets/boring-cities/data.json.

Pipeline per city: load rows -> dedupe -> curation -> geocode -> tiers from coordinates ->
validate -> link status. The shared activity universe is the union of ids across cities; a city that
has no row for an id is `unknown` (not researched yet), never assumed.

Run: uv run scripts/build.py   (exits non-zero on validation errors)
"""

import csv
import json
import sys
from collections import Counter

from common import DATA, SITE, city_rows, cities, km, table

COLUMNS = (
    "id activity category subcategory seed_source doable how venue area lat lon "
    "distance_tier cost_tier beginner_friendly equipment source_url confidence"
).split()
UNIVERSE_COLS = ["id", "activity", "category", "subcategory", "seed_source"]
CATEGORIES = [
    "Sports & Fitness",
    "Outdoors & Nature",
    "Water & Air",
    "Performing Arts & Music",
    "Visual Arts & Crafts",
    "Making & Tech",
    "Games & Mind Sports",
    "Food & Drink",
    "Collecting & Observing",
    "Learning & Culture",
    "Community & Wellness",
    "Extreme & Exotic",
]
ENUMS = {
    "doable": {"yes", "partial", "no"},
    "distance_tier": {"central", "near", "far", "outside", ""},
    "cost_tier": {"free", "$", "$$", "$$$", "$$$$", ""},
    "beginner_friendly": {"y", "n", ""},
    "equipment": {"none", "rent", "own", ""},
    "confidence": {"high", "medium", "low"},
}
CONF_RANK = {"high": 2, "medium": 1, "low": 0}
MAX_KM_FROM_CENTER = 60  # coordinates farther than this are almost certainly wrong


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")


def tier(d):
    return "central" if d < 5 else "near" if d < 15 else "far"


def load(city_id):
    rows, errors, line = [], [], {}
    for r in city_rows("research", city_id):
        batch = r.pop("batch")
        line[batch] = (
            line.get(batch, 1) + 1
        )  # row number within its batch, like the old file line numbers
        if set(r) != set(COLUMNS):
            errors.append(f"{batch}: header mismatch {sorted(r)}")
            break
        r = {k: (v or "").strip() for k, v in r.items()}
        r["id"] = r["id"] or slug(r["activity"])
        if r["doable"] == "no" and not r["confidence"]:
            r["confidence"] = "low"  # structural 'no' from general knowledge, no page
        r["_src"] = f"{batch}:{line[batch]}"
        rows.append(r)
    return rows, errors


def dedupe(rows):
    """Same id in several batches: keep the best-evidenced row (confidence, then source, then venue)."""
    best = {}
    for r in rows:
        key = (
            CONF_RANK.get(r["confidence"], 0),
            bool(r["source_url"]),
            bool(r["venue"]),
        )
        if r["id"] not in best or key > best[r["id"]][0]:
            best[r["id"]] = (key, r)
    if len(rows) != len(best):
        print(f"  dedupe: merged {len(rows) - len(best)} duplicate ids")
    return [r for _, r in best.values()]


def curate(rows, city_id):
    """Apply data/curation.csv (drop / set field) so manual decisions stay auditable."""
    by_id = {r["id"]: r for r in rows}
    for c in city_rows("curation", city_id):
        row = by_id.get(c["id"])
        if row is None:
            print(f"  curation: unknown id {c['id']}")
        elif c["action"] == "drop":
            del by_id[c["id"]]
        elif c["action"] == "set":
            row[c["field"]] = c["value"]
    return list(by_id.values())


def apply_geocode(rows, city_id):
    """Fill blank lat/lon from data/geocode.csv (Nominatim matches accepted by scripts/geocode.py)."""
    geo = {r["id"]: r for r in city_rows("geocode", city_id) if r["lat"]}
    for r in rows:
        g = geo.get(r["id"])
        r["geo"] = ""
        if g and not r["lat"] and g["venue"] == r["venue"]:
            r["lat"], r["lon"], r["geo"] = g["lat"], g["lon"], "nominatim"


def apply_tiers(rows, city):
    """With coordinates, the distance tier is computed, not guessed; `outside` is left alone."""
    for r in rows:
        if r["lat"] and r["distance_tier"] != "outside":
            r["distance_tier"] = tier(
                km(float(r["lat"]), float(r["lon"]), city["lat"], city["lon"])
            )


def apply_link_status(rows, city_id):
    """Mark `verified`: link alive, page mentions the venue (data/url_check.csv), confidence not low."""
    check = {r["id"]: r for r in city_rows("url_check", city_id)}
    for r in rows:
        c = check.get(r["id"], {})
        s = c.get("status", "")
        dead = (
            bool(r["source_url"])
            and bool(s)
            and not (s.startswith("2") or s in ("blocked", "301", "302"))
        )
        mismatch = c.get("match") == "n"
        r["link"] = (
            "dead"
            if dead
            else "mismatch"
            if mismatch
            else ("ok" if r["source_url"] else "")
        )
        r["verified"] = (
            "y" if (r["confidence"] != "low" and not dead and not mismatch) else "n"
        )


def validate(rows, city):
    errors, seen = [], set()
    for r in rows:
        where = f"{city['id']} {r['_src']} ({r['id']})"
        if r["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(r["id"])
        if r["category"] not in CATEGORIES:
            errors.append(f"{where}: bad category {r['category']!r}")
        for col, allowed in ENUMS.items():
            if r[col] not in allowed:
                errors.append(f"{where}: bad {col} {r[col]!r}")
        if r["doable"] in ("yes", "partial") and not r["source_url"].startswith("http"):
            errors.append(f"{where}: {r['doable']} row needs source_url")
        if bool(r["lat"]) != bool(r["lon"]):
            errors.append(f"{where}: lat/lon must come together")
        if r["lat"]:
            try:
                d = km(float(r["lat"]), float(r["lon"]), city["lat"], city["lon"])
                if d > MAX_KM_FROM_CENTER:
                    errors.append(
                        f"{where}: lat/lon {d:.0f} km from {city['name']} centre"
                    )
            except ValueError:
                errors.append(f"{where}: non-numeric lat/lon")
    return errors


def build_city(city):
    rows, errors = load(city["id"])
    rows = curate(dedupe(rows), city["id"])
    apply_geocode(rows, city["id"])
    apply_tiers(rows, city)
    errors += validate(rows, city)
    apply_link_status(rows, city["id"])
    return rows, errors


def main():
    all_cities = [
        {**c, "lat": float(c["lat"]), "lon": float(c["lon"])} for c in cities()
    ]
    has_research = {r["city"] for r in table("research")}
    built, all_errors, universe = {}, [], {}
    for city in all_cities:
        if city["id"] not in has_research:
            continue
        print(city["name"])
        rows, errors = build_city(city)
        all_errors += errors
        built[city["id"]] = rows
        for r in rows:
            universe.setdefault(r["id"], {k: r[k] for k in UNIVERSE_COLS})
    if all_errors:
        print("\n".join(all_errors))
        print(f"{len(all_errors)} validation errors")
        sys.exit(1)

    order = {c: i for i, c in enumerate(CATEGORIES)}
    uni = sorted(
        universe.values(), key=lambda u: (order[u["category"]], u["activity"].lower())
    )
    with open(DATA / "universe.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIVERSE_COLS)
        w.writeheader()
        w.writerows(uni)
    site = SITE
    site.mkdir(parents=True, exist_ok=True)
    out_cities, long_rows = [], []
    for city in all_cities:
        rows = built.get(city["id"])
        if rows is None:
            continue
        acts = {}
        for r in rows:
            d = {k: r[k] for k in COLUMNS if k not in UNIVERSE_COLS}
            d["lat"] = float(d["lat"]) if d["lat"] else None
            d["lon"] = float(d["lon"]) if d["lon"] else None
            d["verified"] = r["verified"] == "y"
            d["link"] = r["link"]
            d["geo"] = r.get("geo", "")
            acts[r["id"]] = d
            long_rows.append({"city": city["id"], **{k: r[k] for k in COLUMNS}})
        v = [
            [r["group"], r["kind"], r["name"], float(r["lat"]), float(r["lon"])]
            for r in city_rows("osm_venues", city["id"])
        ]
        if v:
            (site / f"venues-{city['id']}.json").write_text(
                json.dumps(v, separators=(",", ":"))
            )
        nv = len(v)
        venue_counts = {
            r["group"]: int(r["count"]) for r in city_rows("osm_counts", city["id"])
        }
        out_cities.append(
            {
                "id": city["id"],
                "name": city["name"],
                "country": city["country"],
                "lat": city["lat"],
                "lon": city["lon"],
                "centre": city["centre_name"],
                "venues": nv,
                "venueCounts": venue_counts,
                "notFound": sorted(
                    {
                        r["id"]
                        for r in city_rows("not_found", city["id"])
                        if r["id"] not in acts
                    }
                ),
                "rows": acts,
            }
        )
        c = Counter(r["doable"] for r in rows)
        print(
            f"  {city['name']}: {len(rows)} researched of {len(uni)}: {dict(c)}; {nv} OSM venues"
        )

    (site / "data.json").write_text(
        json.dumps(
            {"categories": CATEGORIES, "universe": uni, "cities": out_cities},
            separators=(",", ":"),
        )
    )
    with open(site / "activities.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["city", *COLUMNS])
        w.writeheader()
        w.writerows(long_rows)


if __name__ == "__main__":
    main()
