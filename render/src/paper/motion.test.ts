import { describe, expect, test } from "vitest";
import { cutEdge, drift, entry, MIN_SCALE, restTilt } from "./motion";

describe("mouvement", () => {
  test("avant son entrée un élément est invisible", () => {
    expect(entry(9, 10).opacity).toBe(0);
  });

  test("l'entrée est fluide, sans paliers, et ne part jamais d'une taille minuscule", () => {
    const frames = Array.from({ length: 40 }, (_, i) => entry(10 + i, 10));
    frames.forEach((e) => expect(e.scale).toBeGreaterThanOrEqual(MIN_SCALE));
    const ys = frames.map((e) => e.y);
    const distinct = new Set(ys.slice(0, 12).map((y) => y.toFixed(3)));
    expect(distinct.size).toBe(12);
    expect(frames[39].opacity).toBe(1);
    expect(Math.abs(frames[39].y)).toBeLessThan(1);
    expect(Math.abs(frames[39].scale - 1)).toBeLessThan(0.01);
  });

  test("le flottement reste de quelques pixels et change à chaque image", () => {
    const xs = Array.from({ length: 120 }, (_, f) => drift("a", f, 3));
    xs.forEach((d) => {
      expect(Math.abs(d.x)).toBeLessThanOrEqual(3);
      expect(Math.abs(d.y)).toBeLessThanOrEqual(3);
    });
    xs.slice(1).forEach((d, i) => expect(Math.abs(d.x - xs[i].x)).toBeLessThan(0.3));
    expect(drift("a", 30).x).not.toBe(drift("b", 30).x);
  });

  test("bords et inclinaisons sont stables pour une même graine", () => {
    expect(cutEdge("x")).toBe(cutEdge("x"));
    expect(cutEdge("x")).not.toBe(cutEdge("y"));
    expect(Math.abs(restTilt("x", 1.6))).toBeLessThanOrEqual(1.6);
  });
});
