/* Apple-Maps-inspired basemap on OpenFreeMap vector tiles (OpenMapTiles schema).
   Adapted from the Walk SG map's style: soft land/park/water colours, white roads with warm casings, quiet labels. */
(() => {
  const THEMES = {
    light: {
      land: "#f4f2ed", landuse: "#ebe8e1", water: "#a9d4f5", waterLine: "#a9d4f5", park: "#cbe6b4", wood: "#bddba6",
      sand: "#f1e7c9", hospital: "#f6dcd8", school: "#efe6d2", building: "#e6e2d9",
      roadMinor: "#ffffff", roadMinorCase: "#dedad1", roadMid: "#ffffff", roadMidCase: "#d4cfc4",
      roadMajor: "#fff0b8", roadMajorCase: "#e3c76a", roadMotor: "#fbd27a", roadMotorCase: "#e0a53e",
      path: "#b9b3a6", rail: "#b5b0a6", label: "#3a3a3f", labelDim: "#7b7b82", halo: "rgba(255,255,255,0.92)", waterLabel: "#4a87b8",
    },
    dark: {
      land: "#1d1e22", landuse: "#222327", water: "#14304a", waterLine: "#14304a", park: "#223a2b", wood: "#1f3527",
      sand: "#2d2b24", hospital: "#33272a", school: "#2a2923", building: "#2d2e34",
      roadMinor: "#3a3b41", roadMinorCase: "#1a1b1e", roadMid: "#44454c", roadMidCase: "#18191c",
      roadMajor: "#6b5f3a", roadMajorCase: "#2a2518", roadMotor: "#8a6d2f", roadMotorCase: "#2a2012",
      path: "#5b5c63", rail: "#55565c", label: "#e6e6ea", labelDim: "#9a9aa3", halo: "rgba(20,21,24,0.9)", waterLabel: "#6fa8d6",
    },
  };

  const FONT = ["Noto Sans Regular"];
  const FONT_BOLD = ["Noto Sans Bold"];
  const NAME = ["coalesce", ["get", "name:en"], ["get", "name"]];
  const w = (base) => ["interpolate", ["exponential", 1.6], ["zoom"], 10, base * 0.25, 14, base, 20, base * 9];
  const src = { source: "openmaptiles" };

  function roadPair(id, filter, fill, casing, width, minzoom = 8) {
    const common = {
      ...src, "source-layer": "transportation", filter, minzoom,
      layout: { "line-cap": "round", "line-join": "round", "line-sort-key": ["to-number", ["get", "layer"], 0] },
    };
    const tunnelFade = ["case", ["==", ["get", "brunnel"], "tunnel"], 0.45, 1];
    return [
      { id: `${id}-case`, type: "line", ...common, paint: { "line-color": casing, "line-width": w(width + 1.6), "line-opacity": tunnelFade } },
      { id, type: "line", ...common, paint: { "line-color": fill, "line-width": w(width), "line-opacity": tunnelFade } },
    ];
  }

  window.makeBasemapStyle = (theme = "light") => {
    const c = THEMES[theme] || THEMES.light;
    const fill = (id, layer, filter, color, extra = {}) => ({ id, type: "fill", ...src, "source-layer": layer, ...(filter ? { filter } : {}), paint: { "fill-color": color, ...extra } });
    const layers = [
      { id: "bg", type: "background", paint: { "background-color": c.land } },
      fill("landcover-wood", "landcover", ["==", "class", "wood"], c.wood, { "fill-opacity": 0.8 }),
      fill("landcover-grass", "landcover", ["in", "class", "grass", "farmland"], c.park, { "fill-opacity": 0.8 }),
      fill("landcover-sand", "landcover", ["==", "class", "sand"], c.sand),
      fill("landuse", "landuse", ["in", "class", "residential", "commercial", "industrial", "retail", "railway", "cemetery"], c.landuse),
      fill("landuse-hospital", "landuse", ["==", "class", "hospital"], c.hospital),
      fill("landuse-school", "landuse", ["in", "class", "school", "university", "college"], c.school),
      fill("landuse-park", "landuse", ["in", "class", "park", "playground", "pitch", "stadium"], c.park),
      fill("park", "park", null, c.park, { "fill-opacity": 0.85 }),
      fill("water", "water", null, c.water),
      { id: "waterway", type: "line", ...src, "source-layer": "waterway", paint: { "line-color": c.waterLine, "line-width": w(1.5) } },

      ...roadPair("road-service", ["all", ["==", "class", "service"]], c.roadMinor, c.roadMinorCase, 2, 14),
      ...roadPair("road-minor", ["in", "class", "minor", "tertiary_link", "secondary_link", "primary_link", "trunk_link", "motorway_link"], c.roadMinor, c.roadMinorCase, 3.4, 12),
      ...roadPair("road-tertiary", ["==", "class", "tertiary"], c.roadMid, c.roadMidCase, 4.8, 11),
      ...roadPair("road-secondary", ["==", "class", "secondary"], c.roadMid, c.roadMidCase, 5.6, 10),
      ...roadPair("road-primary", ["==", "class", "primary"], c.roadMajor, c.roadMajorCase, 6.2, 8),
      ...roadPair("road-trunk", ["==", "class", "trunk"], c.roadMajor, c.roadMajorCase, 6.8, 8),
      ...roadPair("road-motorway", ["==", "class", "motorway"], c.roadMotor, c.roadMotorCase, 7.4, 6),
      { id: "road-path", type: "line", ...src, "source-layer": "transportation", filter: ["in", "class", "path", "pedestrian"], minzoom: 15, paint: { "line-color": c.path, "line-width": w(1.1), "line-dasharray": [1.2, 1.2] } },
      { id: "rail", type: "line", ...src, "source-layer": "transportation", filter: ["in", "class", "rail", "transit"], minzoom: 10, paint: { "line-color": c.rail, "line-width": w(1.2), "line-dasharray": [3, 2] } },

      fill("building", "building", null, c.building, { "fill-opacity": 0.9 }),

      { id: "water-label", type: "symbol", ...src, "source-layer": "water_name", layout: { "text-field": NAME, "text-font": ["Noto Sans Italic"], "text-size": 12, "text-letter-spacing": 0.15 }, paint: { "text-color": c.waterLabel, "text-halo-color": c.halo, "text-halo-width": 1 } },
      { id: "road-label", type: "symbol", ...src, "source-layer": "transportation_name", minzoom: 13, layout: { "text-field": NAME, "text-font": FONT, "text-size": ["interpolate", ["linear"], ["zoom"], 13, 10, 18, 13], "symbol-placement": "line", "text-rotation-alignment": "map" }, paint: { "text-color": c.labelDim, "text-halo-color": c.halo, "text-halo-width": 1.5 } },
      { id: "poi-label", type: "symbol", ...src, "source-layer": "poi", minzoom: 15, filter: ["<=", ["get", "rank"], 18], layout: { "text-field": NAME, "text-font": FONT, "text-size": 11, "text-anchor": "top", "text-offset": [0, 0.6], "text-max-width": 7, "text-optional": true }, paint: { "text-color": c.labelDim, "text-halo-color": c.halo, "text-halo-width": 1.5 } },
      { id: "poi-station", type: "circle", ...src, "source-layer": "poi", minzoom: 13, filter: ["all", ["==", "class", "railway"], ["==", "subclass", "station"]], paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 13, 3, 18, 7], "circle-color": "#ff3b30", "circle-stroke-color": "#fff", "circle-stroke-width": 1.5 } },
      { id: "poi-station-label", type: "symbol", ...src, "source-layer": "poi", minzoom: 13, filter: ["all", ["==", "class", "railway"], ["==", "subclass", "station"]], layout: { "text-field": NAME, "text-font": FONT_BOLD, "text-size": 12, "text-anchor": "left", "text-offset": [0.9, 0], "text-max-width": 8 }, paint: { "text-color": c.label, "text-halo-color": c.halo, "text-halo-width": 1.6 } },
      { id: "place-suburb", type: "symbol", ...src, "source-layer": "place", filter: ["in", "class", "suburb", "neighbourhood", "quarter"], minzoom: 12, maxzoom: 17, layout: { "text-field": NAME, "text-font": FONT_BOLD, "text-size": ["interpolate", ["linear"], ["zoom"], 12, 11, 16, 15], "text-transform": "uppercase", "text-letter-spacing": 0.08, "text-max-width": 8 }, paint: { "text-color": c.labelDim, "text-halo-color": c.halo, "text-halo-width": 1.5 } },
      { id: "place-city", type: "symbol", ...src, "source-layer": "place", filter: ["in", "class", "city", "town", "village", "country", "island"], maxzoom: 14, layout: { "text-field": NAME, "text-font": FONT_BOLD, "text-size": ["interpolate", ["linear"], ["zoom"], 6, 13, 12, 20], "text-max-width": 8 }, paint: { "text-color": c.label, "text-halo-color": c.halo, "text-halo-width": 2 } },
    ];

    return {
      version: 8,
      name: `basemap-${theme}`,
      glyphs: "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
      sources: { openmaptiles: { type: "vector", url: "https://tiles.openfreemap.org/planet", maxzoom: 14 } },
      layers,
    };
  };
})();
