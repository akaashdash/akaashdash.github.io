---
layout: post
title: are cities boring?
date: 2026-10-11
description: Singaporeans keep saying the city is boring. I made a list of 299 hobbies and checked which ones you can do in Singapore, and in twelve other cities.
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

## and twelve other cities

I ran the same list through Hong Kong, Tokyo, London, New York, Atlanta, Sydney, San Francisco, Paris, Chicago, Dubai, Shanghai and Beijing. This is where I have to be careful, because the research isn't equal. Singapore has all 299 activities checked. London has 281, Hong Kong 277, New York 274, Atlanta 264, Tokyo 253, Paris 239, Chicago 238, San Francisco 238, Sydney 221, Dubai 215, Shanghai 193 and Beijing 160. An activity with no result means I couldn't find evidence, which is not the same as "can't be done", and the missing ones tend to be the niche ones. So comparing each city's raw percentage would be unfair. The page only compares activities that have a result in every city you pick.

On the **153 activities with a result in all of the ten best-covered cities**:

| | fully doable | at least partly |
|---|---|---|
| Singapore | 90% | 95% |
| London | 91% | 95% |
| Hong Kong | 88% | 97% |
| New York | 93% | 96% |
| Atlanta | 87% | 95% |
| Tokyo | 83% | 95% |
| Paris | 90% | 95% |
| Chicago | 89% | 94% |
| San Francisco | 88% | 96% |
| Sydney | 84% | 96% |

That's the whole story: a few points either way is noise, and nobody is meaningfully less boring than anybody else. Singapore sits in the middle. (These percentages are higher than the Singapore-only figures above because the shared set leaves out the niche activities that some cities have no evidence for.) The gaps are in the same place everywhere: sports are the weakest broad category at 70 to 78% (the long tail of obscure ones like curling), and the extreme end (snow, caves, canyoning, BASE jumping) is mostly out of reach, because it depends on geography. What differs is mostly geography too: ocean surfing exists in Hong Kong, New York, San Francisco and Sydney but not in Singapore, London, Atlanta, Tokyo, Paris or Chicago. About 41% of the 153 differ in at least one city, but most of those look like holes in my research rather than real absences. There is no reason Tokyo lacks watercolour painting.

Cost and distance look alike as well. Between 63% and 87% of the doable activities in each city are within 15 km of the centre and cheap enough to try on a whim (under about US$45).

Dubai, Shanghai and Beijing are in the explorer too, but I haven't researched them far enough to put in the table. Add them to the comparison and the shared set of activities shrinks, so read those percentages loosely.

## what this doesn't show

- It's not a share of all human hobbies. The list is a sample, seeded from Wikipedia lists plus my own ideas, and I built it while researching Singapore first, so it probably under-counts things only other cities have.
- "Doable" means a venue, club or class exists within about 30 km of the city centre. It doesn't mean it's good, convenient or uncrowded. Cost and distance are rough tiers.
- Research hit a web-search limit repeatedly, so a lot of rows rest on a single listing or aggregator page. Between just under a fifth (New York) and nearly half (Shanghai) of each city's rows are low-confidence. Strict mode on the page counts only rows with a live source link that mentions the venue or activity, which keeps from about 47% (Shanghai) to 75% (New York) of them.
- English-language search and listings find some cities far more easily than others. Beijing and Shanghai in particular are underrepresented because the sources I could reach were thin and dated, so their numbers say more about my search than about those cities.
- "Searched, found nothing" is weaker than it sounds, and a few activities (Peranakan beadwork, Malay dance) are specific to Singapore and weren't searched elsewhere.
- The venue haze on the map is OpenStreetMap, whose completeness differs by city. New York has roughly nine times as many tagged sports facilities as London, which says more about the mapping than the city. Only about half the cities have venue data at all.

If you can think of something that's missing, or something I marked doable that isn't, I want to know. Everything is in the [CSV]({{ '/assets/boring-cities/activities.csv' | relative_url }}).
