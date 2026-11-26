import { describe, expect, test } from "vitest";
import { content, layout, safeWindow } from "../theme";
import { DRIFT_SCALE } from "./SceneFrame";
import { FRAMINGS, framingAt, punchedY, PUNCH_FRAMES, PUNCH_MIN_GAP, punchCuts } from "./punch";

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

  test("même recadrée au maximum, la scène reste dans la zone sûre de TikTok à gauche et à droite", () => {
    const half = (content.width / 2) * layout.safeScale * (1 + DRIFT_SCALE);
    for (const f of FRAMINGS) {
      expect(layout.safeCenterX - half * (1 + f.s) + f.x).toBeGreaterThanOrEqual(safeWindow.left - 12);
      expect(layout.safeCenterX + half * (1 + f.s) + f.x).toBeLessThanOrEqual(safeWindow.right + 12);
    }
  });

  test("un recadrage ne remonte jamais le haut de la scène sous la pastille de chapitre ni le bas sur les sous-titres", () => {
    const center = (layout.stageTop + layout.stageBottom) / 2;
    const half = ((layout.stageBottom - layout.stageTop) / 2) * layout.safeScale * (1 + DRIFT_SCALE);
    for (const f of FRAMINGS) {
      expect(punchedY(center - half, f)).toBeGreaterThanOrEqual(center - half);
      expect(punchedY(center + half, f)).toBeLessThanOrEqual(layout.captionTop);
    }
  });
});
