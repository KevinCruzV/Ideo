import { describe, expect, test } from "vitest";
import { WAVE_BARS, WAVE_FLOOR, waveBars } from "./AudioWave";

describe("onde des extraits audio", () => {
  test("une barre par colonne, la plus récente à droite", () => {
    const levels = [0, 0, 0, 1, 0.5];
    const bars = waveBars(levels, 4);
    expect(bars).toHaveLength(WAVE_BARS);
    expect(bars[WAVE_BARS - 1]).toBeCloseTo(0.5);
    expect(bars[WAVE_BARS - 2]).toBeCloseTo(1);
  });

  test("le silence garde une petite barre visible et rien ne dépasse 1", () => {
    const bars = waveBars([0, 3, -1], 2);
    bars.forEach((b) => {
      expect(b).toBeGreaterThanOrEqual(WAVE_FLOOR);
      expect(b).toBeLessThanOrEqual(1);
    });
  });

  test("avant le début de l'extrait, les barres sont au plancher", () => {
    expect(waveBars([1, 1, 1], 0).slice(0, WAVE_BARS - 1).every((b) => b === WAVE_FLOOR)).toBe(true);
  });
});
