import { describe, expect, test } from "vitest";
import { chapterText } from "./ChapterLabel";
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
