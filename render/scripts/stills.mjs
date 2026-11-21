import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixture = path.resolve(root, process.argv[2] ?? "fixtures/all-scenes.json");
const outDir = path.resolve(root, process.argv[3] ?? "out/stills");
const timeline = JSON.parse(await readFile(fixture, "utf8"));

await mkdir(outDir, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
const composition = await selectComposition({ serveUrl, id: "Short", inputProps: timeline });

for (const [i, segment] of timeline.segments.entries()) {
  const name = segment.kind === "scene" ? segment.type : segment.kind;
  const frame = Math.max(segment.from, segment.to - 3);
  const output = path.join(outDir, `${String(i).padStart(2, "0")}-${name}.png`);
  await renderStill({ composition, serveUrl, inputProps: timeline, frame, output, imageFormat: "png" });
  console.log(path.relative(root, output));
}
