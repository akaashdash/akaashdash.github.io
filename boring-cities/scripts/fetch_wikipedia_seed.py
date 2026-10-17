"""Fetch independent seed candidates from Wikipedia (lists + hobby categories).

Writes data/sources/wikipedia/seed_candidates.csv (title, source) for later curation.
"""

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://en.wikipedia.org/w/api.php"
OUT = (
    Path(__file__).resolve().parent.parent / "data/sources/wikipedia"
)  # raw page dumps; git-ignored, rebuilt by this script
OUT.mkdir(parents=True, exist_ok=True)
LISTS = [
    "List of sports",
    "List of hobbies",
    "List of crafts",
    "List of outdoor activities",
    "List of dance style categories",
    "List of art media",
    "List of performing arts",
    "List of types of martial arts",
    "List of tabletop role-playing games",
    "List of games",
    "List of collectables",
    "List of cooking techniques",
    "List of musical instruments",
    "List of water sports",
    "List of winter sports",
    "List of mind sports",
    "List of extreme sports",
    "List of adventure sports",
    "List of fandom activities",
]
CATEGORIES = [
    "Hobbies",
    "Collecting",
    "Crafts",
    "Recreation",
    "Outdoor recreation",
    "Performing arts",
    "Games",
]


def get(**params):
    url = (
        API
        + "?"
        + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    )
    req = urllib.request.Request(
        url, headers={"User-Agent": "boring-cities/0.1 (research)"}
    )
    for wait in (2, 8, 30, 60):
        time.sleep(1)
        try:
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    raise RuntimeError("rate limited")


rows = []
for page in LISTS:
    d = get(action="parse", page=page, prop="wikitext", redirects=1)
    if "parse" not in d:
        print("missing:", page)
        continue
    text = d["parse"]["wikitext"]
    (OUT / f"{re.sub(r'\W+', '_', page)}.wikitext").write_text(text)
    for m in re.finditer(r"^\*+\s*\[\[([^\]|#]+)", text, re.M):
        rows.append((m.group(1).strip(), f"list:{page}"))
    print("ok:", page, len(text))
for cat in CATEGORIES:
    d = get(
        action="query", list="categorymembers", cmtitle=f"Category:{cat}", cmlimit=500
    )
    for m in d["query"]["categorymembers"]:
        if not m["title"].startswith(("Category:", "List of")):
            rows.append((m["title"], f"category:{cat}"))
seen = {}
for t, s in rows:
    seen.setdefault(t, set()).add(s)
with open(OUT / "seed_candidates.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["title", "sources"])
    for t in sorted(seen):
        w.writerow([t, ";".join(sorted(seen[t]))])
print(len(seen), "unique candidates")
