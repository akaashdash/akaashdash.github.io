"""Build every city: data/cities/<id>/research/*.csv -> activities.csv -> assets/boring-cities/data.json.

Pipeline per city: load batches -> dedupe -> curation.csv -> geocode.csv -> tiers from coordinates ->
validate -> link status. The shared activity universe is the union of ids across cities; a city that
has no row for an id is `unknown` (not researched yet), never assumed.

Run: uv run scripts/build.py   (exits non-zero on validation errors)
"""

import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT.parent / "assets" / "boring-cities"  # the explorer (index.html, app.js, data.json, ...), served by the blog
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


def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = (
        math.sin((lat2 - lat1) * p / 2) ** 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    )
    return 12742 * math.asin(math.sqrt(a))


def tier(d):
    return "central" if d < 5 else "near" if d < 15 else "far"


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def load(city_dir):
    rows, errors = [], []
    for path in sorted((city_dir / "research").glob("*.csv")):
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != COLUMNS:
                errors.append(f"{path.name}: header mismatch {reader.fieldnames}")
                continue
            for i, r in enumerate(reader, 2):
                r = {k: (v or "").strip() for k, v in r.items()}
                r["id"] = r["id"] or slug(r["activity"])
                if r["doable"] == "no" and not r["confidence"]:
                    r["confidence"] = (
                        "low"  # structural 'no' from general knowledge, no page
                    )
                r["_src"] = f"{path.name}:{i}"
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


def curate(rows, city_dir):
    """Apply curation.csv (drop / set field) so manual decisions stay auditable."""
    path = city_dir / "curation.csv"
    if not path.exists():
        return rows
    by_id = {r["id"]: r for r in rows}
    for c in read(path):
        row = by_id.get(c["id"])
        if row is None:
            print(f"  curation: unknown id {c['id']}")
        elif c["action"] == "drop":
            del by_id[c["id"]]
        elif c["action"] == "set":
            row[c["field"]] = c["value"]
    return list(by_id.values())


def apply_geocode(rows, city_dir):
    """Fill blank lat/lon from geocode.csv (Nominatim matches accepted by scripts/geocode.py)."""
    path = city_dir / "geocode.csv"
    geo = {r["id"]: r for r in read(path) if r["lat"]} if path.exists() else {}
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


def apply_link_status(rows, city_dir):
    """Mark `verified`: link alive, page mentions the venue (url_check.csv), confidence not low."""
    path = city_dir / "url_check.csv"
    check = {r["id"]: r for r in read(path)} if path.exists() else {}
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
    city_dir = ROOT / "data/cities" / city["id"]
    rows, errors = load(city_dir)
    rows = curate(dedupe(rows), city_dir)
    apply_geocode(rows, city_dir)
    apply_tiers(rows, city)
    errors += validate(rows, city)
    apply_link_status(rows, city_dir)
    return rows, errors


def main():
    cities = [
        {**c, "lat": float(c["lat"]), "lon": float(c["lon"])}
        for c in read(ROOT / "data/cities.csv")
    ]
    built, all_errors, universe = {}, [], {}
    for city in cities:
        if not (ROOT / "data/cities" / city["id"] / "research").exists():
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
    with open(ROOT / "data/universe.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=UNIVERSE_COLS)
        w.writeheader()
        w.writerows(uni)
    site = SITE
    site.mkdir(exist_ok=True)
    out_cities, long_rows = [], []
    for city in cities:
        rows = built.get(city["id"])
        if rows is None:
            continue
        by_id = {r["id"]: r for r in rows}
        with open(
            ROOT / "data/cities" / city["id"] / "activities.csv", "w", newline=""
        ) as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            for u in uni:
                if u["id"] in by_id:
                    w.writerow({**by_id[u["id"]], **u})
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
        venues = ROOT / "data/cities" / city["id"] / "venues.csv"
        nv = 0
        if venues.exists():
            v = [
                [r["group"], r["kind"], r["name"], float(r["lat"]), float(r["lon"])]
                for r in read(venues)
            ]
            (site / f"venues-{city['id']}.json").write_text(
                json.dumps(v, separators=(",", ":"))
            )
            nv = len(v)
        counts_file = ROOT / "data/cities" / city["id"] / "venue_counts.csv"
        venue_counts = (
            {r["group"]: int(r["count"]) for r in read(counts_file)}
            if counts_file.exists()
            else {}
        )
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
                        for p in (ROOT / "data/cities" / city["id"] / "not_found").glob(
                            "*.csv"
                        )
                        for r in read(p)
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
