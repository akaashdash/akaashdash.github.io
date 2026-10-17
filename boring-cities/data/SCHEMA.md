# Activity data schema

The evidence is `data/research.csv`: the 17 columns below, preceded by `city` and `batch` (the research
round a row came from). Alongside it: `not_found.csv` (city, batch, id, note), `curation.csv` (audited manual
drops/edits), `geocode.csv`, `url_check.csv` and the OpenStreetMap tables `osm_venues.csv`/`osm_counts.csv`;
every table with a `city` column holds all cities. `scripts/build.py` merges, dedupes, curates, validates
and writes `data/universe.csv` and the explorer's files in `assets/boring-cities/` (`data.json`, `activities.csv`).
Cities are listed in `data/cities.csv` (centre coordinates, 25 km radius for the venue map).
`data/RESEARCH_BRIEF.md` is the brief given to research agents.

An activity is identified by `id` across cities (the "universe"). A city with no row for an id is
shown as "not researched", never assumed.

| column | values | notes |
|---|---|---|
| `id` | slug | lowercase-kebab, same id in every city, e.g. `rock-climbing` |
| `activity` | text | human name |
| `category` | one of the 12 categories | below |
| `subcategory` | text | free text, short |
| `seed_source` | e.g. `wikipedia:List of sports` / `brainstorm` | where the idea came from; prefer independent sources |
| `doable` | `yes` / `partial` / `no` | `yes` = the real thing can be done within the metro area (~30 km of the centre); `partial` = only a simulated/indoor/limited/one-off version; `no` = structurally unavailable there (terrain, climate, law, animals). Never `no` merely because nothing was found |
| `how` | one sentence | how/where (or why not), neutral, third person |
| `venue` | text | one real, named example venue/org (blank for `no`) |
| `area` | text | neighbourhood / district of the venue |
| `lat`, `lon` | decimals | venue coordinates only if sure, else blank (build fills from `geocode.csv`) |
| `distance_tier` | `central` / `near` / `far` / `outside` | from the city centre: central <5 km, near 5-15 km, far >15 km, outside = beyond the metro area. Recomputed from coordinates when known |
| `cost_tier` | `free` / `$` / `$$` / `$$$` / `$$$$` | per session, rough, local money: `$` < ~US$15, `$$` 15-45, `$$$` 45-150, `$$$$` > 150. Tiers only |
| `beginner_friendly` | `y` / `n` | can a total novice join a class/session? |
| `equipment` | `none` / `rent` / `own` | `rent` = can rent/borrow on site |
| `source_url` | URL | page evidencing the offering (required for `yes`/`partial`) |
| `confidence` | `high` / `medium` / `low` | high = source page seen confirming it; medium = strong listing, or OpenStreetMap tag (rows in batch `osm`); low = inferred, aggregator or dated |

For `no` rows: leave `venue`, `area`, `lat`, `lon` blank; use `distance_tier` = `outside` when it can be
done somewhere beyond the metro area and name the nearest place and travel time in `how`.

`build.py` also derives, per row: `verified` (link alive per `url_check.csv` and confidence not `low`),
`link` (ok/dead/blank) and `geo` (coordinates from Nominatim).

## Categories (fixed list, exact spelling)

Sports & Fitness | Outdoors & Nature | Water & Air | Performing Arts & Music | Visual Arts & Crafts |
Making & Tech | Games & Mind Sports | Food & Drink | Collecting & Observing | Learning & Culture |
Community & Wellness | Extreme & Exotic
