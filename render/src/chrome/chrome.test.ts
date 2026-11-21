import { describe, expect, test } from "vitest";
import { captionSize } from "./Captions";
import { chapterBottom, chapterFit, chapterText } from "./ChapterLabel";
import { layout } from "../theme";
import { progressTicks } from "./Progress";

const single = { part: 1, total: 1, title: "L'oubli", label: "Partie" };
const series = { part: 2, total: 3, title: "Le sommeil", label: "Partie" };
const segments = [
  { from: 0, to: 90 },
  { from: 90, to: 300 },
  { from: 300, to: 360 },
];

describe("chrome", () => {
  test("une vidéo seule n'affiche que le titre", () => {
    expect(chapterText(single)).toBe("L'oubli");
    expect(chapterText(series)).toBe("Partie 2 · Le sommeil");
  });

  test("le titre de chapitre tient sur deux lignes au-dessus de la scène", () => {
    const long = { part: 8, total: 8, title: "Un titre beaucoup trop long qui ne tiendrait jamais sur une seule ligne du bandeau", label: "Partie" };
    const fit = chapterFit(long);
    expect(fit.lines.length).toBeLessThanOrEqual(2);
    expect(fit.size).toBeLessThan(40);
    expect(chapterBottom(long)).toBeLessThan(layout.stageTop);
    expect(chapterFit(single).size).toBe(40);
    expect(chapterBottom(series)).toBeLessThan(layout.stageTop);
  });

  test("une vidéo seule a un trait par segment", () => {
    const ticks = progressTicks(single, segments, 194, 360);
    expect(ticks.map((t) => t.weight)).toEqual([90, 210, 60]);
    expect(ticks[0].fill).toBe(1);
    expect(ticks[1].fill).toBeCloseTo(0.5, 2);
    expect(ticks[2].fill).toBe(0);
  });

  test("une série garde un trait par partie", () => {
    const ticks = progressTicks(series, segments, 179.5, 360);
    expect(ticks.map((t) => t.fill)).toEqual([1, 0.5, 0]);
  });
});

describe("sous-titres", () => {
  test("un groupe tient sur deux lignes", () => {
    expect(captionSize(["Dis-moi", "pourquoi", "tu", "oublies"])).toBe(76);
    expect(captionSize(["extraordinairement", "incompréhensiblement", "mémorisables"])).toBeLessThan(76);
  });
});
