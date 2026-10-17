"""Review helpers for one city: dead links and weak geocode matches.

Run: uv run scripts/review.py <city>
"""

import re

from common import city_arg, read

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


def words(s):
    return {
        w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP
    }


def main():
    _, cdir = city_arg()
    keep = {r["id"] for r in read(cdir / "activities.csv")}
    if (cdir / "url_check.csv").exists():
        bad = [
            r
            for r in read(cdir / "url_check.csv")
            if r["id"] in keep
            and not r["status"].startswith("2")
            and r["status"] != "blocked"
        ]
        print(f"{len(bad)} dead urls in kept rows")
        for r in bad:
            print(" ", r["status"], r["id"], r["url"][:100])
    if (cdir / "geocode.csv").exists():
        print("weak geocode matches (name overlap < 60%):")
        for r in read(cdir / "geocode.csv"):
            if not r["lat"]:
                continue
            v, m = words(r["venue"].split("(")[0]), words(r["matched_name"])
            frac = len(v & m) / max(1, len(v))
            if frac < 0.6:
                print(
                    f"  {frac:.2f} {r['id']}: {r['venue']!r} -> {r['matched_name']!r}"
                )


if __name__ == "__main__":
    main()
