import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import countries from "i18n-iso-countries";
import { feature } from "topojson-client";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const topo = JSON.parse(readFileSync(path.join(root, "node_modules/world-atlas/countries-50m.json"), "utf8"));
const flagsSource = readFileSync(path.join(root, "src/pictos/flags.ts"), "utf8");
const flagCodes = new Set([...flagsSource.slice(0, flagsSource.indexOf("] as const")).matchAll(/"([a-z]{2})"/g)].map((m) => m[1]));
["eu", "un", "su"].forEach((c) => flagCodes.delete(c));

const SCALE = 200;
const OFFSET_X = 2.74;
const OFFSET_Y = 1.43;

const project = ([lon, lat]) => {
  const l = (lon * Math.PI) / 180;
  const p = (Math.max(-89.9, Math.min(89.9, lat)) * Math.PI) / 180;
  const p2 = p * p;
  const p4 = p2 * p2;
  const x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
  const y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)));
  return [(x + OFFSET_X) * SCALE, (OFFSET_Y - y) * SCALE];
};

const area = (ring) => {
  let a = 0;
  for (let i = 0; i < ring.length; i++) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i + 1) % ring.length];
    a += x1 * y2 - x2 * y1;
  }
  return a / 2;
};

const centroid = (ring) => {
  let cx = 0;
  let cy = 0;
  let a = 0;
  for (let i = 0; i < ring.length; i++) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i + 1) % ring.length];
    const f = x1 * y2 - x2 * y1;
    a += f;
    cx += (x1 + x2) * f;
    cy += (y1 + y2) * f;
  }
  if (Math.abs(a) < 1e-9) return ring[0];
  return [cx / (3 * a), cy / (3 * a)];
};

const thin = (ring, minStep) => {
  const out = [];
  for (const pt of ring) {
    const last = out[out.length - 1];
    if (!last || Math.hypot(pt[0] - last[0], pt[1] - last[1]) >= minStep) out.push(pt);
  }
  return out;
};

const fmt = (v) => (Math.round(v * 10) / 10).toString();

const geo = feature(topo, topo.objects.countries);
const result = {};
for (const f of geo.features) {
  if (f.id === undefined) continue;
  const alpha = countries.numericToAlpha2(String(f.id).padStart(3, "0"));
  if (!alpha) continue;
  const code = alpha.toLowerCase();
  if (!flagCodes.has(code)) continue;
  const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
  const rings = [];
  for (const poly of polys) {
    poly.forEach((source, i) => {
      const crosses = source.some(([lon]) => lon > 170) && source.some(([lon]) => lon < -170);
      const ring = crosses ? source.map(([lon, lat]) => [lon < 0 ? lon + 360 : lon, lat]) : source;
      const full = ring.map(([lon, lat]) => (lon > 180 ? project([180, lat]).map((v, k) => (k === 0 ? v + (lon - 180) * 0.6 : v)) : project([lon, lat])));
      const thinned = thin(full, 0.6);
      const projected = thinned.length >= 4 ? thinned : full;
      if (projected.length < 3) return;
      rings.push({ pts: projected, hole: i > 0, area: Math.abs(area(projected)) });
    });
  }
  if (rings.length === 0) continue;
  const main = rings.filter((r) => !r.hole).sort((a, b) => b.area - a.area)[0];
  const kept = rings.filter((r) => r === main || r.area > 0.06);
  const d = kept.map((r) => `M${r.pts.map(([x, y]) => `${fmt(x)} ${fmt(y)}`).join("L")}Z`).join("");
  const all = kept.flatMap((r) => r.pts);
  const xs = all.map((p) => p[0]);
  const ys = all.map((p) => p[1]);
  const [cx, cy] = centroid(main.pts);
  const entry = {
    d,
    cx: Number(fmt(cx)),
    cy: Number(fmt(cy)),
    size: Number(fmt(Math.hypot(Math.max(...main.pts.map((p) => p[0])) - Math.min(...main.pts.map((p) => p[0])), Math.max(...main.pts.map((p) => p[1])) - Math.min(...main.pts.map((p) => p[1]))))),
    box: [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)].map((v) => Number(fmt(v))),
  };
  if (result[code]) {
    result[code].d += entry.d;
  } else result[code] = entry;
}

const FOCUS = {
  world: [-170, -50, 180, 78],
  europe: [-12, 34, 42, 71],
  africa: [-20, -36, 53, 38],
  asia: [5, -10, 148, 62],
  "north-america": [-130, 5, -55, 72],
  "south-america": [-85, -56, -33, 14],
  "middle-east": [24, 11, 64, 43],
  oceania: [110, -48, 180, -5],
  arctic: [-85, 55, 15, 84],
};

const views = {};
for (const [name, [w, s, e, n]] of Object.entries(FOCUS)) {
  const pts = [];
  for (let i = 0; i <= 40; i++) {
    const lon = w + ((e - w) * i) / 40;
    const lat = s + ((n - s) * i) / 40;
    pts.push(project([lon, s]), project([lon, n]), project([w, lat]), project([e, lat]));
  }
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  views[name] = [Math.min(...xs), Math.min(...ys), Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)].map((v) => Number(fmt(v)));
}

const codes = Object.keys(result).sort();
const lines = [];
for (let i = 0; i < codes.length; i += 14) lines.push(`  ${codes.slice(i, i + 14).map((c) => `"${c}"`).join(", ")},`);
const focusNames = Object.keys(FOCUS);
writeFileSync(
  path.join(root, "src/map/codes.ts"),
  `export const MAP_CODES = [\n${lines.join("\n")}\n] as const;\n\nexport type MapCode = (typeof MAP_CODES)[number];\n\nexport const MAP_FOCUS = [${focusNames.map((f) => `"${f}"`).join(", ")}] as const;\n\nexport type MapFocus = (typeof MAP_FOCUS)[number];\n`,
);
const body = codes.map((c) => `  ${c}: ${JSON.stringify(result[c])},`).join("\n");
writeFileSync(
  path.join(root, "src/map/world.ts"),
  `export type CountryShape = { d: string; cx: number; cy: number; size: number; box: number[] };\n\nexport const COUNTRIES: Record<string, CountryShape> = {\n${body}\n};\n\nexport const VIEWS: Record<string, [number, number, number, number]> = ${JSON.stringify(views)};\n`,
);
console.log(codes.length, "pays", (readFileSync(path.join(root, "src/map/world.ts")).length / 1024).toFixed(0), "Ko");
console.log([...flagCodes].filter((c) => !result[c]).join(" "));
