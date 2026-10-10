---
layout: post
title: is singapore boring?
date: 2026-10-11
description: Singaporeans keep saying the city is boring. I made a list of 299 hobbies and checked which ones you can actually do here.
tags: [singapore, data, maps]
categories: []
---

Singaporeans love to say the city is boring. I don't think that's right, and here's the argument: if a city has things to do, it can't be boring. If you're bored anyway, the problem is you (or us), not the city.

That's testable. Make a very long list of hobbies, crafts, sports and pastimes, then check which ones can actually be done here. If "boring" were true, the list would be full of things Singapore can't offer.

<iframe id="boring-cities" src="{{ '/assets/boring-cities/index.html' | relative_url }}" title="Interactive explorer: which hobbies can you do in Singapore?" style="width:100%;height:1800px;border:0" loading="lazy"></iframe>
<script>
  // The embedded page reports its own height so the iframe never shows an inner scrollbar.
  window.addEventListener("message", (e) => {
    const frame = document.getElementById("boring-cities");
    if (e.source === frame.contentWindow && e.data && e.data.boringCitiesHeight) {
      frame.style.height = e.data.boringCitiesHeight + "px";
    }
  });
</script>

## what I found

Of 299 activities, **227 (76%)** can be done in Singapore as the real thing, and another 38 in a limited form (indoor skiing, simulators, one-off workshops). That's 89% in some form. Only 34 can't be done at all.

Most of the list came from my own head, which would flatter the result. So I also counted just the 156 activities that came from independent Wikipedia lists of sports, games, crafts, dance and collectables. For those, **68%** are fully doable and **84%** at least partly. The honest number is closer to that one.

The shape matters more than the percentage:

- **Where Singapore is rich.** Every food and drink activity, every performing art and every game or mind sport on the list had a taker. So did almost all crafts, from pottery to glassblowing to perfume-making.
- **Where it's thin.** Anything that needs terrain or weather: snow, caves, rapids, mountains, deserts, hunting. In the extreme and exotic category only 10 of 25 were doable, and several of those were simulations. These are real limits, and they're the only reason to say Singapore is *missing* things.
- **It's close and cheap.** About two-thirds of the doable activities are within 15 km of Raffles Place and cost under S$60 a session. 248 of 265 welcome a complete beginner.

Open the map and the thing that stands out is the gray haze: nearly 10,000 venues for sports, parks, arts, crafts, learning and food in OpenStreetMap, spread across the whole island.

## what this doesn't show

- It's not 76% of all human hobbies. The list is a sample, and its composition drives the percentage. That's why the Wikipedia-only figure is the better one to quote.
- "Doable" means a venue, club or class exists. It doesn't mean it's good, convenient or uncrowded. Cost and distance are rough tiers.
- Research hit a search limit part-way, so ideas I couldn't source were left out rather than guessed. Some categories are thinner than I planned, and about a fifth of the rows are low-confidence. Strict mode on the page counts only rows with a live source and medium or higher confidence; the headline barely moves (160 of 210 still fully doable).
- Seeding from Wikipedia reflects what English Wikipedia thinks a hobby is. Local things are probably undercounted.

If you can think of something that's missing, or something I marked doable that isn't, I want to know. Everything is in the [CSV]({{ '/assets/boring-cities/activities.csv' | relative_url }}).
