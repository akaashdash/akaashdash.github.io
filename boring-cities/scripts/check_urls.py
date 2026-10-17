"""Check every source_url of one city -> data/cities/<city>/url_check.csv (id, url, status, match).

status: HTTP code after redirects, `blocked` for 403/429 (page probably exists but refuses bots),
000 when unreachable. match: is the fetched page actually about this row?
  y = page text names the venue (>= 70% of its distinctive words, for at least one alternative
      when the venue lists several separated by / ; or parentheses)
  a = venue not named but the page covers the activity (typical for roundups/listings)
  n = readable Latin text naming neither venue nor activity (likely a mismatched source)
  ? = could not tell (not fetched, or mostly non-Latin text)
Run after build.py: uv run scripts/check_urls.py <city>, then build.py again to apply the results.
"""

import csv
import html
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

from common import city_arg, read

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124 Safari/537.36"
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
    "various",
    "academy",
    "classes",
    "class",
    "workshop",
    "workshops",
}


def tokens(s):
    return {
        w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in STOP
    }


def fetch(url):
    cmd = [
        "curl",
        "-sL",
        "-m",
        "25",
        "-A",
        UA,
        "--max-filesize",
        "3000000",
        "-w",
        "\n%{http_code}",
        url,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=40).stdout.decode(
            "utf-8", "ignore"
        )
    except subprocess.TimeoutExpired:
        return "000", ""
    body, _, code = out.rpartition("\n")
    code = code.strip()
    return ("blocked" if code in ("403", "429") else code or "000"), body


def page_match(venue, activity, body):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text)).lower()
    letters = re.findall(r"[^\W\d_]", text)
    if len(letters) < 200:
        return "?"
    if sum(c.isascii() for c in letters) / len(letters) < 0.6:
        return "?"
    page = set(re.findall(r"[a-z0-9]+", text))
    for a in [a for a in re.split(r"\s*(?:/|;|\(|\))\s*", venue) if tokens(a)]:
        t = tokens(a)
        if len(t & page) / len(t) >= 0.7:
            return "y"
    # Venue not spelled out (roundup/listing pages): still relevant if it covers the activity.
    stems = {w[:5] for w in tokens(activity) if len(w) > 3}
    if stems and any(p.startswith(s) for s in stems for p in page):
        return "a"
    return "n"


def check(row):
    status, body = fetch(row["source_url"])
    match = (
        page_match(row["venue"], row["activity"], body)
        if status.startswith("2")
        else "?"
    )
    return status, match


def main():
    _, cdir = city_arg()
    rows = [r for r in read(cdir / "activities.csv") if r["source_url"]]
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(check, rows))
    with open(cdir / "url_check.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "url", "status", "match"])
        for r, (s, m) in zip(rows, results):
            w.writerow([r["id"], r["source_url"], s, m])
    ok = sum(s.startswith("2") for s, _ in results)
    blocked = sum(s == "blocked" for s, _ in results)
    n = sum(m == "n" for _, m in results)
    y = sum(m == "y" for _, m in results)
    print(
        f"{len(rows)} urls: {ok} ok, {blocked} blocked, {len(rows) - ok - blocked} dead; venue named on page: {y} yes, {n} NO"
    )


if __name__ == "__main__":
    main()
