import { describe, expect, test } from "vitest";
import { enterScale, jitter, stepFrame } from "./stopMotion";

describe("stopMotion", () => {
  test("stepFrame quantise à 12 im/s", () => {
    expect([0, 1, 2, 3, 4, 5].map((f) => stepFrame(f))).toEqual([0, 0, 0, 2.5, 2.5, 5]);
  });

  test("stepFrame respecte fps et stepFps", () => {
    expect(stepFrame(7, 24, 12)).toBe(6);
    expect(stepFrame(9, 30, 10)).toBe(9);
  });

  test("jitter est stable pour un même pas", () => {
    expect(jitter("a", 3)).toBe(jitter("a", 4));
  });

  test("jitter reste dans la limite et varie selon la graine et le pas", () => {
    const values = Array.from({ length: 60 }, (_, f) => jitter("seed", f, 2.5));
    expect(values.every((v) => Math.abs(v) <= 2.5)).toBe(true);
    expect(new Set(values).size).toBeGreaterThan(5);
    expect(jitter("a", 0)).not.toBe(jitter("b", 0));
  });

  test("enterScale entre en trois pas puis reste à 1", () => {
    expect(enterScale(9, 10)).toBe(0);
    expect([10, 11, 12, 13, 14, 15, 16, 30].map((f) => enterScale(f, 10))).toEqual([
      0.4, 0.4, 0.4, 0.75, 0.75, 1, 1, 1,
    ]);
  });
});
