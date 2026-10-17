/* Are cities boring? Interactive explorer.
   Data: data.json {categories, universe, cities[{rows}]}, venues-<city>.json (OSM points). */
(() => {
"use strict";

const COST = ["free", "$", "$$", "$$$", "$$$$"];
const DIST = ["central", "near", "far", "outside"];
const DIST_LABEL = { central: "Central (<5 km)", near: "Near (5–15 km)", far: "Far (>15 km)", outside: "Outside the metro area" };
const LABEL = { yes: "Doable", partial: "Partly (limited / simulated)", no: "Not possible" };
const MIN_ROWS = 50; // a city needs this many researched rows to take part in comparisons

const state = { cat: null, doable: null, q: "", cost: "", dist: "", beginner: false, sort: ["category", 1], open: null };
let DATA, CITY, ALL = [], ACTS = [], VENUES = [];
const venueCache = {};
const $ = (s) => document.querySelector(s);
/* Data files and CSS variables are resolved relative to the script and the .bc wrapper, so the same code runs standalone and inline in a blog post. */
const BASE = document.currentScript.src.replace(/[^/]*$/, "");
// The host page adds ?v=<build> to this script's URL; reuse it on the data files so a new deploy is never served from a stale browser cache.
const VER = new URL(document.currentScript.src).search;
const ROOT = document.querySelector(".bc");
const css = (v) => getComputedStyle(ROOT).getPropertyValue(v).trim();
const color = (d) => css(`--${d}`);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const pct = (a, b) => (b ? Math.round((100 * a) / b) : 0);
const rowsOf = (c) => DATA.universe.filter((u) => c.rows[u.id]).map((u) => ({ ...u, ...c.rows[u.id] }));
const researched = () => DATA.cities.filter((c) => Object.keys(c.rows).length >= MIN_ROWS);

/* ---------- tooltip ---------- */
const tip = $("#tip");
let tipOwner = null; // the element whose hover opened the tooltip
function showTip(html, ev) {
  tipOwner = ev.target || null;
  tip.innerHTML = html;
  tip.hidden = false;
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  tip.style.left = Math.max(8, x) + "px";
  tip.style.top = Math.max(8, y) + "px";
}
const hideTip = () => { tip.hidden = true; tipOwner = null; };
// The tooltip is positioned on the screen, so scrolling moves the page under a still pointer without firing mouseleave.
// Hide it on any scroll, wheel or touch, on Escape and window blur, and once the pointer is no longer over the element that opened it.
addEventListener("scroll", hideTip, { passive: true, capture: true });
addEventListener("wheel", hideTip, { passive: true });
addEventListener("touchstart", hideTip, { passive: true });
addEventListener("blur", hideTip);
addEventListener("keydown", (e) => e.key === "Escape" && hideTip());
document.documentElement.addEventListener("mouseleave", hideTip);
document.addEventListener("pointermove", (e) => { if (!tip.hidden && tipOwner && !tipOwner.contains(e.target)) hideTip(); });
const actTip = (a) =>
  `<b>${esc(a.activity)}</b><br><span class="muted">${esc(a.category)} &middot; ${LABEL[a.doable]}</span>` +
  (a.venue ? `<br>${esc(a.venue)}${a.area ? ", " + esc(a.area) : ""}` : "") +
  (a.cost_tier ? `<br><span class="muted">${esc(a.cost_tier)} &middot; ${esc(a.distance_tier)}</span>` : "") +
  (a.doable === "no" ? `<br><span class="muted">${esc(a.how)}</span>` : "");

/* ---------- filtering ---------- */
function matches(a, { ignoreGrid = false } = {}) {
  if (state.cat && a.category !== state.cat) return false;
  if (state.doable && a.doable !== state.doable) return false;
  if (!ignoreGrid && state.cost && a.cost_tier !== state.cost) return false;
  if (!ignoreGrid && state.dist && a.distance_tier !== state.dist) return false;
  if (state.beginner && a.beginner_friendly !== "y") return false;
  if (state.q) {
    const hay = [a.activity, a.subcategory, a.venue, a.area, a.how, a.category].join(" ").toLowerCase();
    if (!state.q.toLowerCase().split(/\s+/).every((w) => hay.includes(w))) return false;
  }
  return true;
}
const filtered = () => ACTS.filter((a) => matches(a));
const count = (rows) => rows.reduce((c, a) => ((c[a.doable] += 1), c), { yes: 0, partial: 0, no: 0 });

/* ---------- city selection ---------- */
function renderPills() {
  $("#city-pills").innerHTML = DATA.cities
    .filter((c) => Object.keys(c.rows).length)
    .map((c) => `<button class="chip" data-c="${c.id}" aria-pressed="${c.id === CITY.id}">${esc(c.name)}</button>`).join("");
  document.querySelectorAll("#city-pills .chip").forEach((b) => b.addEventListener("click", () => setCity(b.dataset.c)));
}
async function setCity(id) {
  CITY = DATA.cities.find((c) => c.id === id) || DATA.cities[0];
  history.replaceState(null, "", "#" + CITY.id);
  ALL = rowsOf(CITY);
  Object.assign(state, { cat: null, doable: null, q: "", cost: "", dist: "", beginner: false, open: null });
  if ($("#q")) $("#q").value = "";
  ACTS = ALL;
  document.querySelectorAll("#city-name, .cn").forEach((e) => (e.textContent = CITY.name));
  $("#centre-name").textContent = CITY.centre;
  renderPills();
  renderHeadline(); renderNo(); renderMethod();
  await loadVenues();
  renderAll();
  renderCompare();
}

/* ---------- headline ---------- */
function renderHeadline() {
  const n = ACTS.length;
  const c = count(ACTS);
  const gone = DATA.universe.length - ALL.length;
  const nf = Math.min(gone, (CITY.notFound || []).length);
  const todo = gone - nf;
  $("#headline").innerHTML =
    `<span class="big">${pct(c.yes, n)}%</span><span class="cap"><b>${c.yes}</b> of <b>${n}</b> activities can be done in ${esc(CITY.name)}, ` +
    `${c.partial} more in a limited form. Only <b>${c.no}</b> can't.</span>`;
  // Activities with no verdict are left out of the percentages; say so, small, rather than in the headline.
  $("#coverage").textContent = gone
    ? `Not counted: ${[nf && `${nf} searched for without finding a venue`, todo && `${todo} not yet researched`].filter(Boolean).join(", ")}.`
    : "";
  $("#stackbar").setAttribute("aria-label", `${c.yes} doable, ${c.partial} partly, ${c.no} not possible`);
  $("#stackbar").innerHTML = ["yes", "partial", "no"].map((k) => `<span style="flex:${c[k]};background:${color(k)}" title="${LABEL[k]}: ${c[k]}"></span>`).join("");
  $("#legend").innerHTML = ["yes", "partial", "no"].map((k) => `<span><i style="background:${color(k)}"></i>${LABEL[k]} (${c[k]})</span>`).join("");
}

/* ---------- compare (all cities) ---------- */
function commonSet(cities) {
  return DATA.universe.filter((u) => cities.every((c) => c.rows[u.id]));
}
let cmpIds = null;
function renderCompare() {
  const avail = researched();
  $("#s-compare").hidden = avail.length < 2;
  if (avail.length < 2) return;
  // Default: the six best-covered cities (more cities shrink the set of activities they all share); toggle others in.
  if (!cmpIds) cmpIds = [...avail].sort((a, b) => Object.keys(b.rows).length - Object.keys(a.rows).length).slice(0, 6).map((c) => c.id);
  if (cmpIds.length < 2) cmpIds = avail.slice(0, 2).map((c) => c.id);
  const cs = avail.filter((c) => cmpIds.includes(c.id));
  const common = commonSet(cs);
  $("#cmp-pills").innerHTML = avail.map((c) =>
    `<button class="chip" data-c="${c.id}" aria-pressed="${cmpIds.includes(c.id)}">${esc(c.name)} <span class="muted">(${Object.keys(c.rows).length} researched)</span></button>`).join("");
  document.querySelectorAll("#cmp-pills .chip").forEach((b) => b.addEventListener("click", () => {
    const id = b.dataset.c;
    const next = cmpIds.includes(id) ? cmpIds.filter((x) => x !== id) : [...cmpIds, id];
    if (next.length >= 2) { cmpIds = next; renderCompare(); }
  }));
  $("#compare-note").textContent =
    `Choose the cities to compare. To keep it fair, only the ${common.length} activities researched in every chosen city are counted ` +
    `(adding a city with less coverage shrinks that shared set).`;
  renderHeat(cs, common);
  renderDiff(cs, common);
  renderProfile(cs, common);
  renderDensity(cs);
}
function renderHeat(cs, common) {
  const rows = DATA.categories.map((cat) => {
    const items = common.filter((u) => u.category === cat);
    return { cat, n: items.length, cells: cs.map((c) => { const k = count(items.map((u) => c.rows[u.id])); return { c, ...k }; }) };
  }).filter((r) => r.n);
  const total = { cat: "All activities", n: common.length, cells: cs.map((c) => ({ c, ...count(common.map((u) => c.rows[u.id])) })) };
  const head = `<tr><th></th>${cs.map((c) => `<th class="cityh" data-c="${c.id}" tabindex="0">${esc(c.name)}</th>`).join("")}</tr>`;
  const body = [...rows, total].map((r) =>
    `<tr${r === total ? ' class="total"' : ""}><td class="rowh">${esc(r.cat)} <span class="muted">(${r.n})</span></td>` +
    r.cells.map((x) => {
      const p = pct(x.yes, r.n);
      return `<td class="heat" style="background:color-mix(in srgb, var(--yes) ${p * 0.85}%, var(--surface));color:${p > 55 ? "#fff" : "var(--ink)"}" ` +
        `data-tip="${esc(`${x.c.name} · ${r.cat}\n${x.yes} doable, ${x.partial} partly, ${x.no} not possible (of ${r.n})`)}">${p}%</td>`;
    }).join("") + "</tr>").join("");
  const host = $("#heat");
  host.innerHTML = `<div class="table-wrap"><table class="heattable"><thead>${head}</thead><tbody>${body}</tbody></table></div>` +
    `<p class="bnote">Each cell shows the share of activities that can be done as the real thing, and the stronger the blue, the higher that share.</p>`;
  host.querySelectorAll(".cityh").forEach((h) => h.addEventListener("click", () => { setCity(h.dataset.c); $("#s-categories").scrollIntoView({ behavior: "smooth" }); }));
  host.querySelectorAll("td.heat").forEach((td) => {
    td.addEventListener("mousemove", (e) => showTip(esc(td.dataset.tip).replace(/\n/g, "<br>"), e));
    td.addEventListener("mouseleave", hideTip);
  });
}
function renderDiff(cs, common) {
  const ctl = $("#diff-controls");
  if (!ctl.dataset.ready) {
    ctl.dataset.ready = 1;
    ctl.innerHTML = `<select id="diff-a" aria-label="City A"></select><span>has, but</span><select id="diff-b" aria-label="City B"></select><span>doesn't</span>`;
    ["#diff-a", "#diff-b"].forEach((s) => ctl.querySelector(s).addEventListener("change", () => renderCompare()));
  }
  const fill = (sel, keep, fallback) => {
    sel.innerHTML = cs.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
    sel.value = cs.some((c) => c.id === keep) ? keep : fallback;
  };
  const a = $("#diff-a"), b = $("#diff-b");
  const ka = a.value, kb = b.value;
  fill(a, ka, cs.some((c) => c.id === CITY.id) ? CITY.id : cs[0].id); // the open city may not be one of the compared cities
  fill(b, kb, (cs.find((c) => c.id !== a.value) || cs[0]).id);
  const A = cs.find((c) => c.id === a.value), B = cs.find((c) => c.id === b.value);
  const tags = (X, Y, items) => items.map((u) => `<span class="tag" title="${esc(u.category)}: ${esc(Y.rows[u.id].how)}">${esc(u.activity)}</span>`).join("");
  const list = (X, Y) => {
    const has = common.filter((u) => X.rows[u.id].doable === "yes");
    const no = has.filter((u) => Y.rows[u.id].doable === "no");
    const part = has.filter((u) => Y.rows[u.id].doable === "partial");
    return `<div><h4>${esc(X.name)} has it, ${esc(Y.name)} can't (${no.length})</h4>` + (tags(X, Y, no) || `<span class="muted">Nothing.</span>`) +
      `<h4 class="sub">${esc(Y.name)} only has a limited version (${part.length})</h4>` + (tags(X, Y, part) || `<span class="muted">Nothing.</span>`) + "</div>";
  };
  $("#diff").innerHTML = A === B ? `<p class="muted">Pick two different cities.</p>` : list(A, B) + list(B, A);
}
function renderProfile(cs, common) {
  const rows = cs.map((c) => {
    const all = common.map((u) => ({ ...u, ...c.rows[u.id] })), ok = all.filter((a) => a.doable !== "no"), yes = all.filter((a) => a.doable === "yes");
    const near = ok.filter((a) => ["central", "near"].includes(a.distance_tier) && ["free", "$", "$$"].includes(a.cost_tier));
    return `<tr><td class="rowh">${esc(c.name)}</td><td>${all.length}</td><td>${pct(yes.length, all.length)}%</td><td>${pct(ok.length, all.length)}%</td>` +
      `<td>${pct(near.length, ok.length)}%</td><td>${pct(ok.filter((a) => a.beginner_friendly === "y").length, ok.length)}%</td>` +
      `<td>${pct(ok.filter((a) => a.cost_tier === "free" || a.cost_tier === "$").length, ok.length)}%</td></tr>`;
  }).join("");
  $("#profile").innerHTML =
    `<thead><tr><th>City</th><th>Activities compared</th><th>Fully doable</th><th>At least partly</th><th>Within 15 km and under ~US$45</th><th>Beginner-friendly</th><th>Free or very cheap</th></tr></thead><tbody>${rows}</tbody>`;
}
function renderDensity(cs) {
  const groups = [...new Set(cs.flatMap((c) => Object.keys(c.venueCounts || {})))];
  const host = $("#density");
  host.innerHTML = "";
  if (!groups.length) return;
  const rowH = 20, gap = 14, L = 140, W = host.clientWidth || 900, R = 60;
  const max = d3.max(cs.flatMap((c) => groups.map((g) => (c.venueCounts || {})[g] || 0)));
  const x = d3.scaleSqrt([0, max], [L, W - R]);
  const H = groups.length * (cs.length * rowH + gap + 18);
  const svg = d3.select(host).append("svg").attr("width", W).attr("height", H).attr("role", "img").attr("aria-label", "Venue counts by type and city");
  groups.forEach((g, gi) => {
    const y0 = gi * (cs.length * rowH + gap + 18);
    svg.append("text").attr("x", 0).attr("y", y0 + 13).style("font-size", "13px").style("font-weight", 600).text(g);
    cs.forEach((c, ci) => {
      const v = (c.venueCounts || {})[g];
      const y = y0 + 18 + ci * rowH;
      svg.append("text").attr("x", L - 8).attr("y", y + 13).attr("text-anchor", "end").style("font-size", "12px").text(c.name);
      if (v === undefined) {
        svg.append("text").attr("x", L + 4).attr("y", y + 13).style("font-size", "11.5px").style("font-style", "italic").text("n/a (count not fetched)");
        return;
      }
      svg.append("rect").attr("x", L).attr("y", y + 2).attr("width", Math.max(1, x(v) - L)).attr("height", rowH - 5).attr("rx", 3).attr("fill", color("yes"))
        .on("mousemove", (e) => showTip(`<b>${esc(c.name)}</b><br>${esc(g)}: ${v.toLocaleString()}`, e)).on("mouseleave", hideTip);
      svg.append("text").attr("x", x(v) + 6).attr("y", y + 13).style("font-size", "11.5px").text(v.toLocaleString());
    });
  });
}

/* ---------- category chart ---------- */
function renderCategories() {
  const host = $("#cat-chart");
  host.innerHTML = "";
  const rows = DATA.categories
    .map((cat) => {
      const items = ACTS.filter((a) => a.category === cat);
      return { cat, n: items.length, ...count(items) };
    })
    .filter((r) => r.n)
    .sort((a, b) => b.yes / b.n - a.yes / a.n);
  const W = host.clientWidth || 900, L = Math.min(190, W * 0.34), R = 56, H = 22, G = 12;
  // Wrap a label onto at most two lines so it is never clipped by the chart edge (approximate text width: 0.56em per character).
  const wrapLabel = (s, maxChars) => {
    if (s.length <= maxChars) return [s];
    const words = s.split(" ");
    let best = [s], bestMax = Infinity;
    for (let i = 1; i < words.length; i++) {
      const a = words.slice(0, i).join(" "), b = words.slice(i).join(" ");
      if (Math.max(a.length, b.length) < bestMax) { best = [a, b]; bestMax = Math.max(a.length, b.length); }
    }
    return best;
  };
  const svg = d3.select(host).append("svg").attr("width", W).attr("height", rows.length * (H + G) + 4).attr("role", "img")
    .attr("aria-label", `Share of activities doable in ${CITY.name}, by category`);
  const x = d3.scaleLinear([0, 1], [L, W - R]);
  rows.forEach((r, i) => {
    const g = svg.append("g").attr("transform", `translate(0,${i * (H + G)})`).style("cursor", "pointer")
      .attr("opacity", !state.cat || state.cat === r.cat ? 1 : 0.35).attr("tabindex", 0).attr("role", "button")
      .attr("aria-pressed", state.cat === r.cat)
      .on("click", () => toggleCat(r.cat))
      .on("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggleCat(r.cat)));
    const lines = wrapLabel(r.cat, Math.floor((L - 14) / (13 * 0.56)));
    const label = g.append("text").attr("x", L - 12).attr("text-anchor", "end").style("font-size", "13px");
    lines.forEach((ln, k) => label.append("tspan").attr("x", L - 12).attr("y", H / 2 + (k - (lines.length - 1) / 2) * 14).attr("dy", "0.35em").text(ln));
    let acc = 0;
    ["yes", "partial", "no"].forEach((k) => {
      const w = x(r[k] / r.n) - x(0);
      if (!r[k]) return;
      g.append("rect").attr("x", x(acc / r.n)).attr("y", 0).attr("width", Math.max(0, w - 2)).attr("height", H)
        .attr("rx", 3).attr("fill", color(k))
        .on("mousemove", (e) => showTip(`<b>${esc(r.cat)}</b><br>${LABEL[k]}: ${r[k]} of ${r.n}`, e)).on("mouseleave", hideTip);
      acc += r[k];
    });
    g.append("text").attr("x", W - R + 8).attr("y", H / 2).attr("dy", "0.35em").style("font-size", "12.5px").text(`${r.yes}/${r.n}`);
  });
}
function toggleCat(c) {
  state.cat = state.cat === c ? null : c;
  renderAll();
}

/* ---------- treemap ---------- */
/* One square per activity, grouped by category and sorted doable -> partly -> not, so each group reads as a bar. */
function renderTreemap() {
  const host = $("#treemap");
  const order = { yes: 0, partial: 1, no: 2 };
  host.replaceChildren(...DATA.categories.flatMap((cat) => {
    const items = ACTS.filter((a) => a.category === cat).sort((a, b) => order[a.doable] - order[b.doable] || a.activity.localeCompare(b.activity));
    if (!items.length) return [];
    const group = document.createElement("div");
    group.className = "wcat" + (state.cat && state.cat !== cat ? " dim" : "");
    const head = document.createElement("button");
    head.className = "wh";
    head.innerHTML = `<b>${esc(cat)}</b><span>${items.filter((a) => a.doable === "yes").length} of ${items.length}</span>`;
    head.addEventListener("click", () => toggleCat(cat));
    const cells = document.createElement("div");
    cells.className = "cells";
    items.forEach((a) => {
      const c = document.createElement("button");
      c.className = `cell ${a.doable}`;
      c.setAttribute("aria-label", `${a.activity}: ${LABEL[a.doable]}`);
      c.addEventListener("mousemove", (e) => showTip(actTip(a), e));
      c.addEventListener("mouseleave", hideTip);
      c.addEventListener("focus", (e) => { const r = c.getBoundingClientRect(); showTip(actTip(a), { clientX: r.right, clientY: r.top }); });
      c.addEventListener("blur", hideTip);
      c.addEventListener("click", () => focusRow(a.id));
      cells.append(c);
    });
    group.append(head, cells);
    return [group];
  }));
}

/* ---------- map ---------- */
let map, venueLayers = {}, pinLayer, ringLayer, venueGroup;
const isDark = () => css("color-scheme") === "dark";
let vectorBase;
// Vector basemap has its own light/dark style; the raster fallback is darkened with a CSS filter instead.
function syncMapTheme() {
  if (!map) return;
  if (vectorBase) vectorBase.getMaplibreMap().setStyle(makeBasemapStyle(isDark() ? "dark" : "light"));
  else $("#map").classList.toggle("dark-tiles", isDark());
}
function initMap() {
  map = L.map("map", { preferCanvas: true, scrollWheelZoom: false }).setView([CITY.lat, CITY.lon], 11);
  // Vector basemap (Apple-Maps-style palette from basemap.js on OpenFreeMap tiles); fall back to raster OSM tiles if MapLibre didn't load or WebGL is unavailable.
  const attribution = '<a href="https://openfreemap.org" target="_blank" rel="noopener">OpenFreeMap</a> &copy; <a href="https://www.openmaptiles.org/" target="_blank" rel="noopener">OpenMapTiles</a> data from <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>';
  const webgl = (() => { try { const c = document.createElement("canvas"); return !!(c.getContext("webgl2") || c.getContext("webgl")); } catch { return false; } })();
  // The CSP build loads its worker from a same-origin file, so it works on hosts that forbid blob: workers (like the blog).
  if (window.maplibregl) maplibregl.setWorkerUrl(`${BASE}maplibre-gl-csp-worker.min.js${VER}`);
  if (L.maplibreGL && webgl && window.makeBasemapStyle) {
    vectorBase = L.maplibreGL({ style: makeBasemapStyle(isDark() ? "dark" : "light"), attribution });
    vectorBase.addTo(map);
  } else {
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution, maxZoom: 18 }).addTo(map);
    if (!webgl) $("#map").insertAdjacentHTML("afterend", `<p class="bnote">Showing the standard map because WebGL is off in this browser. Turn on graphics acceleration (Chrome: Settings, System) and reload for the styled map.</p>`);
  }
  syncMapTheme();
  ringLayer = L.layerGroup().addTo(map);
  venueGroup = L.layerGroup().addTo(map);
  pinLayer = L.layerGroup().addTo(map);
}
async function loadVenues() {
  if (!(CITY.id in venueCache)) {
    try { venueCache[CITY.id] = await (await fetch(`${BASE}venues-${CITY.id}.json${VER}`)).json(); } catch { venueCache[CITY.id] = []; }
  }
  VENUES = venueCache[CITY.id];
  if (!map) initMap();
  const c = [CITY.lat, CITY.lon];
  map.setView(c, 11);
  ringLayer.clearLayers();
  [5000, 15000].forEach((r) => L.circle(c, { radius: r, color: css("--ink-3"), weight: 1, dashArray: "4 4", fill: false, interactive: false }).addTo(ringLayer)
    .bindTooltip(`${r / 1000} km`, { permanent: true, direction: "top", className: "ring" }));
  L.circleMarker(c, { radius: 5, color: css("--ink"), fillColor: css("--ink"), fillOpacity: 1 }).addTo(ringLayer).bindTooltip(`${CITY.centre} (centre)`);
  venueGroup.clearLayers();
  venueLayers = {};
  const ctl = $("#map-controls");
  ctl.innerHTML = "";
  [...new Set(VENUES.map((v) => v[0]))].forEach((g) => {
    const pts = VENUES.filter((v) => v[0] === g);
    venueLayers[g] = L.layerGroup(pts.map((v) =>
      L.circleMarker([v[3], v[4]], { radius: 1.6, stroke: false, fillColor: css("--no"), fillOpacity: 0.3 })
        .bindTooltip(`${esc(v[2] || v[1])}<br><span style="opacity:.7">${esc(g)}</span>`)));
    const id = "g-" + g.replace(/\W/g, "");
    ctl.insertAdjacentHTML("beforeend", `<label><input type="checkbox" id="${id}" checked> ${esc(g)} (${(CITY.venueCounts[g] || pts.length).toLocaleString()})</label>`);
    $("#" + id).addEventListener("change", (e) => (e.target.checked ? venueLayers[g].addTo(venueGroup) : venueGroup.removeLayer(venueLayers[g])));
    venueLayers[g].addTo(venueGroup);
  });
}
function renderPins() {
  if (!map) return;
  pinLayer.clearLayers();
  filtered().filter((a) => a.lat != null).forEach((a) => {
    L.circleMarker([a.lat, a.lon], { radius: 6, color: css("--bg"), weight: 1.5, fillColor: color(a.doable), fillOpacity: 0.95 })
      .bindPopup(`<b>${esc(a.activity)}</b><br>${esc(a.venue)}<br>${a.source_url ? `<a href="${esc(a.source_url)}" target="_blank" rel="noopener">source</a>` : ""}`)
      .addTo(pinLayer);
  });
}

/* ---------- cost x distance grid ---------- */
const COST_LABEL = { free: ["Free", "no cost"], "$": ["$", "under US$15"], "$$": ["$$", "US$15 to 45"], "$$$": ["$$$", "US$45 to 150"], "$$$$": ["$$$$", "over US$150"] };
const DIST_NAME = { central: ["Central", "under 5 km"], near: ["Near", "5 to 15 km"], far: ["Far", "over 15 km"], outside: ["Outside", "beyond the metro area"] };
const mk = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
/* Cost tier (columns) by distance (rows). Plain HTML so labels wrap and a cell grows to fit its dots instead of clipping them. */
function renderGrid() {
  const items = ACTS.filter((a) => a.doable !== "no" && COST.includes(a.cost_tier) && DIST.includes(a.distance_tier) && matches(a, { ignoreGrid: true }));
  const dists = DIST.filter((d) => items.some((a) => a.distance_tier === d));
  const table = mk("div", "gt");
  table.setAttribute("role", "group");
  table.setAttribute("aria-label", "Doable activities by cost tier and distance from the centre");
  table.append(mk("div", "gt-corner"), ...COST.map((c) => mk("div", "gt-col", `<b>${COST_LABEL[c][0]}</b><span>${COST_LABEL[c][1]}</span>`)));
  dists.forEach((d) => {
    table.append(mk("div", "gt-row", `<b>${DIST_NAME[d][0]}</b><span>${DIST_NAME[d][1]}</span>`));
    COST.forEach((c) => {
      const cell = items.filter((a) => a.cost_tier === c && a.distance_tier === d).sort((a, b) => a.doable.localeCompare(b.doable) || a.activity.localeCompare(b.activity));
      const box = mk("div", "gt-cell" + (state.cost === c && state.dist === d ? " on" : ""));
      if (cell.length) {
        const n = mk("button", "gt-n", `${cell.length}`);
        n.setAttribute("aria-label", `${cell.length} activities, ${COST_LABEL[c][0]}, ${DIST_NAME[d][0]}. Filter the table to these.`);
        n.addEventListener("click", () => { Object.assign(state, { cost: c, dist: d }); renderAll(); $("#s-table").scrollIntoView({ behavior: "smooth" }); });
        const dots = mk("div", "gt-dots");
        cell.forEach((a) => {
          const b = mk("button", `gdot ${a.doable}`);
          b.setAttribute("aria-label", `${a.activity}: ${LABEL[a.doable]}`);
          b.addEventListener("mousemove", (e) => showTip(actTip(a), e));
          b.addEventListener("mouseleave", hideTip);
          b.addEventListener("focus", () => { const r = b.getBoundingClientRect(); showTip(actTip(a), { clientX: r.right, clientY: r.top }); });
          b.addEventListener("blur", hideTip);
          b.addEventListener("click", () => focusRow(a.id));
          dots.append(b);
        });
        box.append(n, dots);
      }
      table.append(box);
    });
  });
  $("#grid").replaceChildren(table);
}

/* ---------- the "no" list ---------- */
function renderNo() {
  $("#nolist").innerHTML = ACTS.filter((a) => a.doable === "no")
    .map((a) => `<div><b>${esc(a.activity)}</b><span>${esc(a.how)}</span></div>`).join("") || `<p class="muted">Nothing on the list is impossible here.</p>`;
}

/* ---------- table ---------- */
const COLS = [
  ["activity", "Activity"], ["category", "Category"], ["doable", "Doable"], ["venue", "Example venue"], ["area", "Area"],
  ["cost_tier", "Cost"], ["distance_tier", "Distance"], ["beginner_friendly", "Beginner"],
];
function renderFilters() {
  const f = $("#filters");
  if (f.dataset.ready) return syncFilters();
  f.dataset.ready = 1;
  f.innerHTML =
    `<input id="q" type="search" placeholder="Search activities, venues, areas…" aria-label="Search">` +
    ["yes", "partial", "no"].map((k) => `<button class="chip" data-d="${k}" aria-pressed="false"><span class="dot" style="background:${color(k)}"></span>${LABEL[k].split(" (")[0]}</button>`).join("") +
    `<select id="f-cat" aria-label="Category"><option value="">All categories</option>${DATA.categories.map((c) => `<option>${esc(c)}</option>`).join("")}</select>` +
    `<select id="f-cost" aria-label="Cost"><option value="">Any cost</option>${COST.map((c) => `<option>${c}</option>`).join("")}</select>` +
    `<select id="f-dist" aria-label="Distance"><option value="">Any distance</option>${DIST.map((d) => `<option value="${d}">${DIST_LABEL[d]}</option>`).join("")}</select>` +
    `<button class="chip" id="f-beg" aria-pressed="false">Beginner-friendly</button><button class="chip" id="f-reset">Reset</button>`;
  $("#q").addEventListener("input", (e) => { state.q = e.target.value; renderTable(); renderPins(); renderGrid(); });
  f.querySelectorAll("[data-d]").forEach((b) => b.addEventListener("click", () => { state.doable = state.doable === b.dataset.d ? null : b.dataset.d; renderAll(); }));
  $("#f-cat").addEventListener("change", (e) => { state.cat = e.target.value || null; renderAll(); });
  $("#f-cost").addEventListener("change", (e) => { state.cost = e.target.value; renderAll(); });
  $("#f-dist").addEventListener("change", (e) => { state.dist = e.target.value; renderAll(); });
  $("#f-beg").addEventListener("click", () => { state.beginner = !state.beginner; renderAll(); });
  $("#f-reset").addEventListener("click", () => { Object.assign(state, { cat: null, doable: null, q: "", cost: "", dist: "", beginner: false }); $("#q").value = ""; renderAll(); });
  syncFilters();
}
function syncFilters() {
  document.querySelectorAll("#filters [data-d]").forEach((b) => b.setAttribute("aria-pressed", state.doable === b.dataset.d));
  $("#f-cat").value = state.cat || "";
  $("#f-cost").value = state.cost;
  $("#f-dist").value = state.dist;
  $("#f-beg").setAttribute("aria-pressed", state.beginner);
}
function renderTable() {
  const [key, dir] = state.sort;
  const order = { yes: 0, partial: 1, no: 2 };
  const catIdx = (a) => DATA.categories.indexOf(a.category);
  const val = (a) => key === "doable" ? order[a.doable] : key === "category" ? catIdx(a) : key === "cost_tier" ? COST.indexOf(a.cost_tier) : key === "distance_tier" ? DIST.indexOf(a.distance_tier) : String(a[key]).toLowerCase();
  const rows = filtered().sort((a, b) => {
    const va = val(a), vb = val(b);
    return (va < vb ? -1 : va > vb ? 1 : a.activity.localeCompare(b.activity)) * dir;
  });
  const t = $("#table");
  t.innerHTML =
    `<thead><tr>${COLS.map(([k, l]) => `<th data-k="${k}" aria-sort="${state.sort[0] === k ? (dir > 0 ? "ascending" : "descending") : "none"}">${l}${state.sort[0] === k ? (dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("")}</tr></thead><tbody>` +
    rows.map((a) => {
      const open = state.open === a.id;
      return `<tr class="arow ${open ? "hl" : ""}" data-id="${a.id}" id="r-${a.id}" tabindex="0"><td>${esc(a.activity)}</td><td>${esc(a.category)}</td>` +
        `<td><span class="dot" style="background:${color(a.doable)}"></span>${a.doable}</td><td>${esc(a.venue)}</td><td>${esc(a.area)}</td>` +
        `<td>${esc(a.cost_tier)}</td><td>${esc(a.distance_tier)}</td><td>${esc(a.beginner_friendly)}</td></tr>` +
        (open ? `<tr class="detail"><td colspan="8">${esc(a.how)}<br>` +
          `${a.source_url ? `<a href="${esc(a.source_url)}" target="_blank" rel="noopener">source</a> &middot; ` : ""}confidence: ${esc(a.confidence)} &middot; equipment: ${esc(a.equipment || "n/a")} &middot; seed: ${esc(a.seed_source)}</td></tr>` : "");
    }).join("") + "</tbody>";
  t.querySelectorAll("th").forEach((th) => th.addEventListener("click", () => {
    const k = th.dataset.k;
    state.sort = [k, state.sort[0] === k ? -state.sort[1] : 1];
    renderTable();
  }));
  t.querySelectorAll("tr.arow").forEach((tr) => {
    const toggle = () => { state.open = state.open === tr.dataset.id ? null : tr.dataset.id; renderTable(); };
    tr.addEventListener("click", toggle);
    tr.addEventListener("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggle()));
  });
  $("#table-count").textContent = `${rows.length} of ${ACTS.length} activities shown.`;
}
function focusRow(id) {
  Object.assign(state, { cat: null, doable: null, q: "", cost: "", dist: "", beginner: false, open: id });
  $("#q").value = "";
  renderAll();
  const row = $("#r-" + id);
  if (row) row.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------- footer ---------- */
function renderMethod() {
  const seeds = {};
  ACTS.forEach((a) => { const k = a.seed_source.split(":")[0]; seeds[k] = (seeds[k] || 0) + 1; });
  const conf = ACTS.filter((a) => a.confidence === "high").length;
  $("#method").innerHTML =
    `${DATA.universe.length} activities in the shared list: ${seeds.wikipedia || 0} (in ${esc(CITY.name)}) were drawn from independent Wikipedia lists and categories (sports, games, crafts, dance, collectables and more) and ${seeds.brainstorm || 0} were brainstormed. ` +
    `The list was assembled while researching Singapore first, so it may under-represent things only other cities have. ` +
    `Each activity was then searched for in ${esc(CITY.name)} and, where found, tied to a venue, club or class with a source link. ` +
    `${conf} rows are high-confidence (source page seen); the rest are inferred or lower confidence and flagged in the table. Research ran out of search budget in places, so ideas that couldn't be sourced were left out rather than guessed, and some categories are thin. ` +
    `Cost tiers are rough (about <US$15 / 15–45 / 45–150 / 150+ per session). ` +
    `Venue points on the map come from OpenStreetMap (ODbL). "Doable" means the real thing exists within the metro area; "partly" means an indoor, simulated or limited version.`;
}

/* ---------- boot ---------- */
function renderAll() {
  renderCategories(); renderTreemap(); renderGrid(); renderPins(); renderFilters(); renderTable();
}
async function boot() {
  DATA = await (await fetch(`${BASE}data.json${VER}`)).json();
  const start = DATA.cities.find((c) => c.id === location.hash.slice(1)) || DATA.cities.find((c) => c.id === "singapore") || DATA.cities[0];
  CITY = start;
  await setCity(start.id);
  let t;
  addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { renderCategories(); renderTreemap(); renderGrid(); renderCompare(); }, 150); });
  const restyle = () => { renderHeadline(); renderAll(); renderCompare(); syncMapTheme(); };
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", restyle);
  // A host page (e.g. a blog) switches theme by setting data-theme on <html>.
  new MutationObserver(restyle).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
}

boot();
})();
