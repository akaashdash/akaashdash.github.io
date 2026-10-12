---
layout: post
title: are cities boring?
date: 2026-10-11
description: Singaporeans keep saying the city is boring. I made a list of 299 hobbies, checked which ones you can do in Singapore, then in Hong Kong, Tokyo, London, New York and Atlanta.
tags: [singapore, data, maps]
categories: []
---

Singaporeans love to say the city is boring. I don't think that's right, and here's the argument: if a city has things to do, it can't be boring. If you're bored anyway, the problem is you (or us), not the city.

That's testable. Make a very long list of hobbies, crafts, sports and pastimes, then check which ones can actually be done here. If "boring" were true, the list would be full of things Singapore can't offer. Then do the same for other cities, to see whether Singapore is unusual.

<iframe id="boring-cities" src="{{ '/assets/boring-cities/index.html' | relative_url }}" title="Interactive explorer: which hobbies can you do in each city?" style="width:100%;height:1800px;border:0" loading="lazy"></iframe>
<script>
  // The embedded page reports its own height so the iframe never shows an inner scrollbar.
  window.addEventListener("message", (e) => {
    const frame = document.getElementById("boring-cities");
    if (e.source === frame.contentWindow && e.data && e.data.boringCitiesHeight) {
      frame.style.height = e.data.boringCitiesHeight + "px";
    }
  });
</script>

## singapore first

Of 299 activities, **227 (76%)** can be done in Singapore as the real thing, and another 38 in a limited form (indoor skiing, simulators, one-off workshops). That's 89% in some form. Only 34 can't be done at all.

Most of the list came from my own head, which would flatter the result. So I also counted just the 156 activities that came from independent Wikipedia lists of sports, games, crafts, dance and collectables. For those, **68%** are fully doable and **84%** at least partly. The honest number is closer to that one.

The shape matters more than the percentage:

- **Where Singapore is rich.** Every food and drink activity, every performing art and every game or mind sport on the list had a taker. So did almost all crafts, from pottery to glassblowing to perfume-making.
- **Where it's thin.** Anything that needs terrain or weather: snow, caves, rapids, mountains, deserts, hunting. In the extreme and exotic category only 10 of 25 were doable, and several of those were simulations.
- **It's close and cheap.** About 70% of the doable activities are within 15 km of Raffles Place and cost under S$60 a session. 248 of 265 welcome a complete beginner.

## and five other cities

I ran the same list through Hong Kong, Tokyo, London, New York and Atlanta. This is where I have to be careful, because the research isn't equal. Singapore has all 299 activities checked, Atlanta 220, Hong Kong 217, London 215, Tokyo 206 and New York 197. An activity with no row means "not researched", never "no". The ones I couldn't evidence tend to be the niche ones, so comparing each city's raw percentage would be unfair. The page only compares activities researched in every city you pick.

On the **122 activities researched in all six cities**:

| | fully doable |
|---|---|
| Singapore | 76% |
| Hong Kong | 76% |
| Tokyo | 75% |
| London | 79% |
| New York | 80% |
| Atlanta | 73% |

That's the whole story: with 122 activities, a few points either way is noise. No city is meaningfully less boring than the others, and Singapore sits in the middle. The gaps are in the same place everywhere. Every city is at 90% or above on games, learning and the performing arts, at 59 to 70% on sports (the long tail of obscure ones like curling or sepak takraw), and at 8% or less on the extreme end (snow, caves, canyoning, BASE jumping), because those depend on geography. What differs is mostly geography too: ocean surfing and whale or dolphin watching exist in Hong Kong and New York but not in the other four, natural hot springs only in Tokyo, ice hockey everywhere except Singapore. A good number of the remaining differences (improv comedy in Hong Kong, bread baking in Atlanta, CNC machining in Singapore) look more like gaps in my research than real absences, so I wouldn't read anything into them.

Cost and distance look alike as well. Between 63% and 86% of the doable activities in each city are within 15 km of the centre and cheap enough to try on a whim (under about US$45).

## what this doesn't show

- It's not a share of all human hobbies. The list is a sample, seeded from Wikipedia lists plus my own ideas, and I built it while researching Singapore first, so it probably under-counts things only other cities have.
- "Doable" means a venue, club or class exists within about 30 km of the city centre. It doesn't mean it's good, convenient or uncrowded. Cost and distance are rough tiers.
- Research hit a web-search limit repeatedly, which is why coverage is uneven. Between about a sixth (New York) and two fifths (Atlanta) of each city's rows are low-confidence. Strict mode on the page counts only rows with a live source link that mentions the venue or activity, which keeps about 60 to 76% of them.
- The venue haze on the map is OpenStreetMap, whose completeness differs by city. New York has roughly nine times as many tagged sports facilities as London, which says more about the mapping than the city. Atlanta's venue map didn't finish loading, and London is missing two categories.
- Seeding from English Wikipedia reflects what English Wikipedia thinks a hobby is, and English-language search may find Singapore, London, New York and Atlanta venues more easily than Tokyo ones.

If you can think of something that's missing, or something I marked doable that isn't, I want to know. Everything is in the [CSV]({{ '/assets/boring-cities/activities.csv' | relative_url }}).
