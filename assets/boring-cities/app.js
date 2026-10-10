/* Is Singapore boring? Interactive explorer. Data: data.json (activities), venues.json (OSM points). */
"use strict";

const COST = ["free", "$", "$$", "$$$", "$$$$"];
const DIST = ["central", "near", "far", "off-island"];
const DIST_LABEL = { central: "Central (<5 km)", near: "Near (5–15 km)", far: "Far (>15 km)", "off-island": "Off-island" };
const CBD = [1.2842, 103.851]; // Raffles Place
const LABEL = { yes: "Doable", partial: "Partly (limited / simulated)", no: "Not possible" };

const state = { cat: null, doable: null, q: "", cost: "", dist: "", beginner: false, sort: ["category", 1], open: null };
let DATA, VENUES = [], ACTS = [], strict = false;
const $ = (s) => document.querySelector(s);
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const color = (d) => css(`--${d}`);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

/* ---------- tooltip ---------- */
const tip = $("#tip");
function showTip(html, ev) {
  tip.innerHTML = html;
  tip.hidden = false;
  const r = tip.getBoundingClientRect();
  let x = ev.clientX + 14, y = ev.clientY + 14;
  if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - 14;
  if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - 14;
  tip.style.left = Math.max(8, x) + "px";
  tip.style.top = Math.max(8, y) + "px";
}
const hideTip = () => (tip.hidden = true);
const actTip = (a) =>
  `<b>${esc(a.activity)}</b><br><span class="muted">${esc(a.category)} &middot; ${LABEL[a.doable]}</span>` +
  (a.venue ? `<br>${esc(a.venue)}${a.area ? ", " + esc(a.area) : ""}` : "") +
  (a.cost_tier ? `<br><span class="muted">${esc(a.cost_tier)} &middot; ${esc(a.distance_tier)}</span>` : "") +
  (a.doable === "no" ? `<br><span class="muted">${esc(a.how)}</span>` : "");

/* ---------- filtering ---------- */
function matches(a, { ignoreCat = false, ignoreGrid = false } = {}) {
  if (!ignoreCat && state.cat && a.category !== state.cat) return false;
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

/* ---------- headline ---------- */
function renderHeadline() {
  const n = ACTS.length;
  const c = { yes: 0, partial: 0, no: 0 };
  ACTS.forEach((a) => c[a.doable]++);
  const pct = Math.round((100 * c.yes) / n);
  $("#headline").innerHTML =
    `<span class="big">${pct}%</span><span class="cap"><b>${c.yes}</b> of <b>${n}</b> activities can be done in Singapore, ` +
    `${c.partial} more in a limited form. Only <b>${c.no}</b> can't.</span>`;
  const wiki = ACTS.filter((a) => a.seed_source.startsWith("wikipedia"));
  const wy = wiki.filter((a) => a.doable === "yes").length, wp = wiki.filter((a) => a.doable === "partial").length;
  $("#seedline").innerHTML =
    `Fairer test: counting only the ${wiki.length} activities that came from independent Wikipedia lists (not my own ideas), ` +
    `<b>${Math.round((100 * wy) / wiki.length)}%</b> are fully doable and <b>${Math.round((100 * (wy + wp)) / wiki.length)}%</b> at least partly.`;
  const bar = $("#stackbar");
  bar.setAttribute("aria-label", `${c.yes} doable, ${c.partial} partly, ${c.no} not possible`);
  bar.innerHTML = ["yes", "partial", "no"].map((k) => `<span style="flex:${c[k]};background:${color(k)}" title="${LABEL[k]}: ${c[k]}"></span>`).join("");
  $("#legend").innerHTML = ["yes", "partial", "no"].map((k) => `<span><i style="background:${color(k)}"></i>${LABEL[k]} (${c[k]})</span>`).join("");
}

/* ---------- category chart ---------- */
function renderCategories() {
  const host = $("#cat-chart");
  host.innerHTML = "";
  const rows = DATA.categories
    .map((cat) => {
      const items = ACTS.filter((a) => a.category === cat);
      const c = { yes: 0, partial: 0, no: 0 };
      items.forEach((a) => c[a.doable]++);
      return { cat, n: items.length, ...c };
    })
    .filter((r) => r.n)
    .sort((a, b) => b.yes / b.n - a.yes / a.n);
  const W = host.clientWidth || 900, L = Math.min(190, W * 0.34), R = 56, H = 28, G = 8;
  const svg = d3.select(host).append("svg").attr("width", W).attr("height", rows.length * (H + G) + 4).attr("role", "img")
    .attr("aria-label", "Share of activities doable in Singapore, by category");
  const x = d3.scaleLinear([0, 1], [L, W - R]);
  rows.forEach((r, i) => {
    const g = svg.append("g").attr("transform", `translate(0,${i * (H + G)})`).style("cursor", "pointer")
      .attr("opacity", !state.cat || state.cat === r.cat ? 1 : 0.35).attr("tabindex", 0).attr("role", "button")
      .attr("aria-pressed", state.cat === r.cat)
      .on("click", () => toggleCat(r.cat))
      .on("keydown", (e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggleCat(r.cat)));
    g.append("text").attr("x", L - 10).attr("y", H / 2).attr("dy", "0.35em").attr("text-anchor", "end").style("font-size", "13.5px").text(r.cat);
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
function renderTreemap() {
  const host = $("#treemap");
  host.innerHTML = "";
  const W = host.clientWidth || 900, H = Math.max(640, Math.min(980, W * 1.0));
  const root = d3.hierarchy({
    children: DATA.categories.map((c) => ({ name: c, children: ACTS.filter((a) => a.category === c).map((a) => ({ name: a.activity, a, value: 1 })) })).filter((c) => c.children.length),
  }).sum((d) => d.value || 0).sort((a, b) => b.value - a.value);
  d3.treemap().size([W, H]).paddingOuter(2).paddingTop((d) => (d.depth === 1 ? 17 : 0)).paddingInner(1.5).round(true)(root);
  const svg = d3.select(host).append("svg").attr("width", W).attr("height", H).attr("role", "img").attr("aria-label", "Treemap of all activities colored by doability");
  root.children.forEach((cat) => {
    const dim = state.cat && state.cat !== cat.data.name;
    const g = svg.append("g").attr("opacity", dim ? 0.3 : 1);
    g.append("text").attr("x", cat.x0 + 3).attr("y", cat.y0 + 12).style("font-size", "11.5px").style("font-weight", 600)
      .style("cursor", "pointer").text(cat.data.name).on("click", () => toggleCat(cat.data.name));
    cat.leaves().forEach((l) => {
      const a = l.data.a, w = l.x1 - l.x0, h = l.y1 - l.y0;
      const cell = g.append("g").style("cursor", "pointer")
        .on("mousemove", (e) => showTip(actTip(a), e)).on("mouseleave", hideTip).on("click", () => focusRow(a.id));
      cell.append("rect").attr("x", l.x0).attr("y", l.y0).attr("width", w).attr("height", h).attr("rx", 2).attr("fill", color(a.doable));
      if (w > 56 && h > 24) {
        cell.append("clipPath").attr("id", "c-" + a.id).append("rect").attr("x", l.x0).attr("y", l.y0).attr("width", w).attr("height", h);
        cell.append("text").attr("clip-path", `url(#c-${a.id})`).attr("x", l.x0 + 4).attr("y", l.y0 + 13).style("font-size", "10.5px")
          .style("fill", a.doable === "no" ? "#0b0b0b" : "#fff").style("pointer-events", "none").text(a.activity);
      }
    });
  });
}

/* ---------- map ---------- */
let map, venueLayers = {}, pinLayer;
function initMap() {
  map = L.map("map", { preferCanvas: true, scrollWheelZoom: false }).setView([1.3521, 103.8198], 11);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors', maxZoom: 18,
  }).addTo(map);
  const syncTheme = () => $("#map").classList.toggle("dark-tiles", isDark());
  syncTheme();
  [5000, 15000].forEach((r) => L.circle(CBD, { radius: r, color: css("--ink-3"), weight: 1, dashArray: "4 4", fill: false, interactive: false }).addTo(map)
    .bindTooltip(`${r / 1000} km`, { permanent: true, direction: "top", className: "ring" }));
  L.circleMarker(CBD, { radius: 5, color: css("--ink"), fillColor: css("--ink"), fillOpacity: 1 }).addTo(map).bindTooltip("Raffles Place (CBD)");

  const groups = [...new Set(VENUES.map((v) => v[0]))];
  const ctl = $("#map-controls");
  groups.forEach((g) => {
    const pts = VENUES.filter((v) => v[0] === g);
    venueLayers[g] = L.layerGroup(pts.map((v) =>
      L.circleMarker([v[3], v[4]], { radius: 2.2, stroke: false, fillColor: css("--no"), fillOpacity: 0.45 })
        .bindTooltip(`${esc(v[2] || v[1])}<br><span style="opacity:.7">${esc(g)}</span>`)));
    const id = "g-" + g.replace(/\W/g, "");
    ctl.insertAdjacentHTML("beforeend", `<label><input type="checkbox" id="${id}" checked> ${esc(g)} (${pts.length})</label>`);
    $("#" + id).addEventListener("change", (e) => (e.target.checked ? venueLayers[g].addTo(map) : map.removeLayer(venueLayers[g])));
    venueLayers[g].addTo(map);
  });
  pinLayer = L.layerGroup().addTo(map);
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncTheme);
}
const isDark = () => css("color-scheme") === "dark";
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
function renderGrid() {
  const host = $("#grid");
  host.innerHTML = "";
  const items = ACTS.filter((a) => a.doable !== "no" && COST.includes(a.cost_tier) && DIST.includes(a.distance_tier) && matches(a, { ignoreGrid: true }));
  const W = host.clientWidth || 900, L = 110, T = 24, cw = (W - L) / COST.length, rh = 120;
  const dists = DIST.filter((d) => items.some((a) => a.distance_tier === d));
  const svg = d3.select(host).append("svg").attr("width", W).attr("height", T + rh * dists.length + 4).attr("role", "img")
    .attr("aria-label", "Doable activities by cost tier and distance from the CBD");
  COST.forEach((c, i) => svg.append("text").attr("x", L + i * cw + cw / 2).attr("y", 14).attr("text-anchor", "middle").style("font-size", "13px").text(c === "free" ? "Free" : c));
  dists.forEach((d, j) => {
    svg.append("text").attr("x", L - 10).attr("y", T + j * rh + rh / 2).attr("text-anchor", "end").attr("dy", "0.35em").style("font-size", "12.5px").text(DIST_LABEL[d]);
    COST.forEach((c, i) => {
      const cell = items.filter((a) => a.cost_tier === c && a.distance_tier === d).sort((a, b) => a.doable.localeCompare(b.doable) || a.activity.localeCompare(b.activity));
      const x0 = L + i * cw, y0 = T + j * rh;
      const g = svg.append("g");
      g.append("rect").attr("x", x0 + 2).attr("y", y0 + 2).attr("width", cw - 4).attr("height", rh - 4).attr("rx", 4)
        .attr("fill", css("--surface")).style("cursor", "pointer")
        .on("click", () => { Object.assign(state, { cost: c, dist: d }); renderAll(); $("#s-table").scrollIntoView({ behavior: "smooth" }); });
      if (!cell.length) return;
      const pad = 8, w = cw - 4 - 2 * pad, h = rh - 4 - 2 * pad - 12;
      const s = Math.min(14, Math.max(4, Math.floor(Math.sqrt((w * h) / cell.length))));
      const cols = Math.max(1, Math.floor(w / s));
      cell.forEach((a, k) => {
        g.append("circle").attr("cx", x0 + 2 + pad + (k % cols) * s + s / 2).attr("cy", y0 + 2 + pad + 12 + Math.floor(k / cols) * s + s / 2)
          .attr("r", Math.max(1.8, s / 2 - 1.2)).attr("fill", color(a.doable)).style("cursor", "pointer")
          .on("mousemove", (e) => showTip(actTip(a), e)).on("mouseleave", hideTip).on("click", () => focusRow(a.id));
      });
      g.append("text").attr("x", x0 + 2 + pad).attr("y", y0 + 2 + pad + 8).style("font-size", "11px").style("pointer-events", "none").text(cell.length);
    });
  });
}

/* ---------- the "no" list ---------- */
function renderNo() {
  $("#nolist").innerHTML = ACTS.filter((a) => a.doable === "no")
    .map((a) => `<div><b>${esc(a.activity)}</b><span>${esc(a.how)}</span></div>`).join("");
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
  const rows = filtered().sort((a, b) => {
    const va = key === "doable" ? order[a.doable] : key === "category" ? catIdx(a) : key === "cost_tier" ? COST.indexOf(a.cost_tier) : key === "distance_tier" ? DIST.indexOf(a.distance_tier) : String(a[key]).toLowerCase();
    const vb = key === "doable" ? order[b.doable] : key === "category" ? catIdx(b) : key === "cost_tier" ? COST.indexOf(b.cost_tier) : key === "distance_tier" ? DIST.indexOf(b.distance_tier) : String(b[key]).toLowerCase();
    return (va < vb ? -1 : va > vb ? 1 : a.activity.localeCompare(b.activity)) * dir;
  });
  const t = $("#table");
  t.innerHTML =
    `<thead><tr>${COLS.map(([k, l]) => `<th data-k="${k}" aria-sort="${state.sort[0] === k ? (dir > 0 ? "ascending" : "descending") : "none"}">${l}${state.sort[0] === k ? (dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("")}</tr></thead><tbody>` +
    rows.map((a) => {
      const open = state.open === a.id;
      return `<tr class="row ${open ? "hl" : ""}" data-id="${a.id}" id="r-${a.id}" tabindex="0"><td>${esc(a.activity)}</td><td>${esc(a.category)}</td>` +
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
  t.querySelectorAll("tr.row").forEach((tr) => {
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
  $("#r-" + id)?.scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------- footer ---------- */
function renderMethod() {
  const seeds = {};
  ACTS.forEach((a) => (seeds[a.seed_source.split(":")[0]] = (seeds[a.seed_source.split(":")[0]] || 0) + 1));
  const conf = ACTS.filter((a) => a.confidence === "high").length;
  $("#method").innerHTML =
    `${ACTS.length} activities: ${seeds.wikipedia || 0} were drawn from independent Wikipedia lists and categories (sports, games, crafts, dance, collectables and more) and ${seeds.brainstorm || 0} were brainstormed, ` +
    `which is why the Wikipedia-only figure above is the fairer one. Each activity was then searched for in Singapore and, where found, tied to a venue, club or class with a source link. ` +
    `${conf} rows are high-confidence (source page seen); the rest are inferred or lower confidence and flagged in the table. Research ran out of search budget partway, so ideas that couldn't be sourced were left out rather than guessed, and some categories are thin. ` +
    `Cost tiers are rough (<S$20 / 20–60 / 60–200 / 200+ per session). ` +
    `Venue points on the map come from OpenStreetMap (ODbL). "Doable" means the real thing exists here; "partly" means an indoor, simulated or limited version.`;
}

/* ---------- boot ---------- */
function renderAll() {
  renderCategories(); renderTreemap(); renderGrid(); renderPins(); renderFilters(); renderTable();
  window.reportHeight?.();
}
async function boot() {
  DATA = await (await fetch("data.json")).json();
  ACTS = DATA.activities;
  $("#strict").addEventListener("change", (e) => {
    strict = e.target.checked;
    ACTS = strict ? DATA.activities.filter((a) => a.verified) : DATA.activities;
    renderHeadline(); renderNo(); renderMethod(); renderAll();
  });
  $("#strict-label").textContent = `Strict mode: only rows with a live source and medium/high confidence (${DATA.activities.filter((a) => a.verified).length} of ${DATA.activities.length})`;
  try { VENUES = await (await fetch("venues.json")).json(); } catch { VENUES = []; }
  renderHeadline(); renderNo(); renderMethod();
  initMap();
  renderAll();
  let t;
  addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { renderCategories(); renderTreemap(); renderGrid(); }, 150); });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { renderHeadline(); renderAll(); });
}
/* ---------- embedding: follow the host blog's theme, report height for iframe auto-resize ---------- */
if (window.self !== window.top) {
  let theme = "light";
  try { theme = window.parent.document.documentElement.getAttribute("data-theme") || "light"; } catch { /* cross-origin host */ }
  document.documentElement.dataset.theme = theme;
  document.documentElement.classList.add("embedded");
  // Body height (not documentElement.scrollHeight, which never drops below the iframe's own height).
  const post = () => window.parent.postMessage({ boringCitiesHeight: Math.ceil(document.body.getBoundingClientRect().height) + 32 }, "*");
  window.reportHeight = post;
  new ResizeObserver(post).observe(document.body);
  addEventListener("load", post);
}
boot();
