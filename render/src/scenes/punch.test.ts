import { describe, expect, test } from "vitest";
import { FRAMINGS, framingAt, PUNCH_FRAMES, PUNCH_MIN_GAP, punchCuts } from "./punch";

describe("recadrages", () => {
  test("un recadrage par élément, ni collé au début ni à la fin, jamais deux trop proches", () => {
    expect(punchCuts([5, 40, 50, 90, 200, 295], 300)).toEqual([40, 90, 200]);
    const cuts = punchCuts([30, 31, 32, 60, 61, 120], 300);
    cuts.slice(1).forEach((c, i) => expect(c - cuts[i]).toBeGreaterThanOrEqual(PUNCH_MIN_GAP));
  });

  test("le cadre change net à chaque coupe puis tient", () => {
    const cuts = [40, 100];
    expect(framingAt(cuts, 0)).toEqual(FRAMINGS[0]);
    expect(framingAt(cuts, 40 + PUNCH_FRAMES).s).toBeCloseTo(FRAMINGS[1].s);
    expect(framingAt(cuts, 90).s).toBeCloseTo(FRAMINGS[1].s);
    expect(framingAt(cuts, 100 + PUNCH_FRAMES).s).toBeCloseTo(FRAMINGS[2].s);
  });
});
