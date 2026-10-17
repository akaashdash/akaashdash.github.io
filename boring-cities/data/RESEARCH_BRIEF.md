# Research brief: one city, one chunk

Goal: for a blog post testing "is <city> boring?", record for each activity in `data/universe.csv`
whether it can be done in <city>, with evidence. Singapore is already done
(`data/cities/singapore/activities.csv`); read it first to see the expected style and level of detail.
Column definitions and enums: `data/SCHEMA.md`. Output uses the same 17 columns.

## Chunks (by `category` in universe.csv)

- **A**: Sports & Fitness, Water & Air, Extreme & Exotic
- **B**: Outdoors & Nature, Performing Arts & Music, Visual Arts & Crafts, Collecting & Observing
- **C**: Making & Tech, Games & Mind Sports, Food & Drink, Learning & Culture, Community & Wellness

## Output

Write `data/cities/<city-id>/research/<chunk>.csv` (header exactly as SCHEMA.md). One row per
universe activity in your chunk: copy `id, activity, category, subcategory, seed_source` verbatim from
universe.csv. **Write incrementally**: save the file after every ~10 activities so partial work
survives. Do not add activities that are not in universe.csv. Skip an activity (no row) rather than guess:
a missing row is shown as "not researched", which is honest; an invented venue is not.

## Definitions (same for every city, so comparisons are fair)

- The city is the metro area around its centre (see `data/cities.csv`). `doable=yes` means the real
  thing can be done at a venue/club/class within roughly 30 km of the centre.
- `partial` = only a limited, simulated, indoor, informal or one-off version (e.g. ski simulator,
  occasional workshop).
- `no` = structurally impossible or unavailable within the metro area (needs terrain, climate, animals,
  a law that does not exist). Use `distance_tier=outside` when it exists elsewhere, and mention the
  nearest place and rough travel time in `how`. Never use `no` just because a search found nothing;
  if you cannot establish availability either way, skip the row.
- `distance_tier`: central <5 km, near 5-15 km, far >15 km from the centre, outside = beyond the metro
  area. If you give `lat`/`lon` the build recomputes the tier from them.
- `cost_tier` per typical session in local money: **free**, `$` (<~US$15), `$$` (15-45), `$$$` (45-150),
  `$$$$` (>150). Tiers only; never invent exact prices.
- `venue` = one real, named example. `area` = neighbourhood/district. `lat`/`lon` only if you are sure
  (leave blank otherwise; coordinates are geocoded later from the venue name).
- `source_url` is required for yes/partial and must be a page you actually opened that shows the
  offering exists. Prefer the operator's own page. `confidence`: high = you read a page confirming it;
  medium = strong secondary source/listing; low = inferred or dated.
- `how` is one sentence, neutral, no first person ("I"), no "this session".

## Tools and budget

- WebSearch has a **shared budget across all researchers**. Use at most ~1 search per activity, group
  where sensible (e.g. one search covering several martial arts), and prefer `WebFetch` on a known
  operator page or Wikipedia page. If WebSearch starts refusing, continue with WebFetch/curl and your
  own knowledge of well-known venues, but only write rows whose source_url you fetched successfully.
- Local-language sources are fine. Report names in English (with the local name in parentheses if
  helpful).
- Use `uv`, never plain python/pip. Do not touch any file other than your output CSV.

## Report

Reply with: rows written, yes/partial/no counts, how many activities were skipped and why, and any
systematic issue. Keep it short.

## Gap-fill pass (second round) - READ THIS, it relaxes the evidence rule

The first round skipped too much: obvious activities (piano lessons, cricket, yoga) were left blank because a
single page returned 403 or search came back thin. A missing row makes the city look worse than it is, so in
this pass **write a row whenever you can point to real evidence**, graded by `confidence`:

- **high**: you opened an operator/authority page that shows the offering.
- **medium**: a WebSearch result (title/snippet/URL) names a specific operator, venue, club or class offering
  it, even if you could not open the page. Use that result URL as `source_url`.
- **low**: only a roundup/listing/aggregator mention, or an old page. Still write the row.
- If you have found nothing at all after one search, **skip** (never invent). Do not mark `no` for
  "nothing found"; `no` still needs a structural reason (terrain, climate, law, animals).

Budget: the search limit is shared with other researchers, so spend about **one search per 2-4 related
activities** (e.g. "ballet OR contemporary dance classes <city>"), reading all listed operators from the one
result. WebFetch/curl on known pages does not use the search budget, so prefer it for confirmation.

Input: `data/cities/<city>/gaps.csv` (activities still missing; ids already covered by OpenStreetMap
evidence in `research/osm.csv` are excluded). Your slice is given by row range in your prompt. Output:
`data/cities/<city>/research/gaps-<n>.csv`, same 17-column schema, written incrementally. All other
definitions above still apply (metro area within ~30 km of the centre, tiers, `how` neutral and third person).
Fill `cost_tier`, `beginner_friendly`, `equipment` where you can (the user wants full metadata).

## Recording "searched, nothing found" (final round)

For every activity in your slice you must end up with exactly one of:

1. a row in your research CSV (evidence found), or
2. a row in `data/cities/<city>/not_found/<your-file-name>.csv` with header `id,note`, where `note` says in
   a few words what you tried (e.g. `searched "tango classes Atlanta"; only a 2013 post`).

This separates "looked and found nothing" from "never looked". It is NOT a claim that the activity is
impossible there; never use it for structural impossibility (that is a `no` row). Write both files
incrementally. If you run out of search budget, leave the rest of your slice unlisted (not yet searched).

A "not found" entry is only valid after a real search or a page that loaded; if every attempt failed to
load, leave the activity unlisted instead. Meetup keyword pages such as
`https://www.meetup.com/find/?keywords=<activity>&location=gb--London` fetched reliably with WebFetch in
London (the most useful non-search source there) but returned nothing for Hong Kong, so test one first.

Search tips from earlier rounds: the search tool ignores OR operators and often answers only the first theme,
so use one specific query per activity for the stubborn ones (e.g. `ikebana classes Atlanta`), try the local
language for Tokyo/Hong Kong, search for the typical operator type (`<activity> club <city>`, `<activity>
meetup <city>`, `<activity> workshop <city>`), and check Meetup/Eventbrite/Wikipedia pages with WebFetch.

Rule for the new-city rounds: a `not_found` note must say what you SEARCHED (start it with `searched "<query>"`).
Entries justified only by a Meetup/Eventbrite keyword page loading are automatically pruned (those pages match
loosely and mostly list events), so don't write them; leave the activity unlisted instead. The web-search pool is
shared and can run out quickly, so spend your searches on the highest-value activities first (mainstream ones
you could not confirm any other way) and use WebFetch (Wikipedia, operator pages, class directories) for the rest.

Class-directory shortcut (no search budget): in Sydney, the community-college course search pages
(e.g. `sydneycommunitycollege.com.au/courses?s=pottery`) loaded with WebFetch and evidenced ~25 craft, art
and music activities at high confidence. Look for the equivalent in your city: community/adult-education
colleges, council or park-district course catalogues, Skillshare/Eventbrite-style class directories, city
tourism pages. Try several keyword searches on one directory instead of using WebSearch.
