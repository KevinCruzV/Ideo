import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args.splice(i, 2)[1] : undefined;
};
const framesArg = flag("--frames");
const jobs = args[0]
  ? [{ fixture: args[0], outDir: args[1] ?? "out/stills" }]
  : [
      { fixture: "fixtures/all-scenes.json", outDir: "out/stills" },
      { fixture: "fixtures/parts.json", outDir: "out/stills/parts" },
      { fixture: "fixtures/mascot-poses.json", outDir: "out/stills/mascot" },
    ];

const EXIT = 6;
const momentsOf = (segment) => {
  const length = segment.to - segment.from;
  return [
    ["a-debut", segment.from + 2],
    ["b-milieu", segment.from + Math.round(length / 2)],
    ["c-fin", Math.max(segment.from + 2, segment.to - EXIT - 6)],
  ];
};

const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
const browser = await openBrowser("chrome");

for (const job of jobs) {
  const timeline = JSON.parse(await readFile(path.resolve(root, job.fixture), "utf8"));
  const outDir = path.resolve(root, job.outDir);
  await mkdir(outDir, { recursive: true });
  const composition = await selectComposition({ serveUrl, id: "Short", inputProps: timeline, puppeteerInstance: browser });
  const shots = framesArg
    ? framesArg.split(",").map((f) => [`f${String(Number(f)).padStart(5, "0")}`, Number(f)])
    : timeline.segments.flatMap((segment, i) => {
        const base = segment.kind === "scene" ? segment.type : segment.kind;
        const pose = typeof segment.props?.pose === "string" ? `-${segment.props.pose}` : "";
        return momentsOf(segment).map(([moment, frame]) => [`${String(i).padStart(2, "0")}-${base}${pose}-${moment}`, frame]);
      });
  for (const [name, frame] of shots) {
    const output = path.join(outDir, `${name}.png`);
    await renderStill({ composition, serveUrl, inputProps: timeline, frame, output, imageFormat: "png", puppeteerInstance: browser });
    console.log(path.relative(root, output));
  }
}
await browser.close({ silent: true });
