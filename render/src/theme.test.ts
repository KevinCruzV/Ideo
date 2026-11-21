import { describe, expect, test } from "vitest";
import { accentAt, accentForIndex } from "./theme";

describe("accent", () => {
  test("rotation rouge, jaune, bleu par index de segment", () => {
    expect([0, 1, 2, 3, 4, 13].map(accentForIndex)).toEqual(["red", "yellow", "blue", "red", "yellow", "yellow"]);
    expect(accentForIndex(Number.NaN)).toBe("red");
  });

  test("accentAt suit le segment courant", () => {
    const spans = [
      { from: 0, to: 10, accent: accentForIndex(0) },
      { from: 10, to: 20, accent: accentForIndex(1) },
    ];
    expect(accentAt(spans, 5)).toBe("red");
    expect(accentAt(spans, 12)).toBe("yellow");
    expect(accentAt(spans, 99)).toBe("red");
  });
});
