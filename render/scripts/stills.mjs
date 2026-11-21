import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const jobs = process.argv[2]
  ? [{ fixture: process.argv[2], outDir: process.argv[3] ?? "out/stills" }]
  : [
      { fixture: "fixtures/all-scenes.json", outDir: "out/stills" },
      { fixture: "fixtures/parts.json", outDir: "out/stills/parts" },
      { fixture: "fixtures/mascot-poses.json", outDir: "out/stills/mascot" },
    ];

const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });

for (const job of jobs) {
  const timeline = JSON.parse(await readFile(path.resolve(root, job.fixture), "utf8"));
  const outDir = path.resolve(root, job.outDir);
  await mkdir(outDir, { recursive: true });
  const composition = await selectComposition({ serveUrl, id: "Short", inputProps: timeline });
  for (const [i, segment] of timeline.segments.entries()) {
    const base = segment.kind === "scene" ? segment.type : segment.kind;
    const pose = typeof segment.props?.pose === "string" ? `-${segment.props.pose}` : "";
    const name = `${base}${pose}`;
    const frame = Math.max(segment.from, segment.to - 3);
    const output = path.join(outDir, `${String(i).padStart(2, "0")}-${name}.png`);
    await renderStill({ composition, serveUrl, inputProps: timeline, frame, output, imageFormat: "png" });
    console.log(path.relative(root, output));
  }
}
