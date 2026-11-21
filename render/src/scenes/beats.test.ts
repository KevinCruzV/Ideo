import { describe, expect, test } from "vitest";
import { BEAT_FRAMES, beatAt, localBeats } from "./beats";

describe("temps forts", () => {
  test("les images absolues deviennent locales, triées, dans la scène", () => {
    expect(localBeats([150, 120, 999, -5, "x"], 100, 200)).toEqual([20, 50]);
    expect(localBeats(undefined, 0, 10)).toEqual([]);
  });

  test("une réaction dure le temps prévu, puis s'arrête", () => {
    const beats = [20, 50];
    expect(beatAt(beats, 19)).toBeNull();
    expect(beatAt(beats, 20)?.index).toBe(0);
    expect(beatAt(beats, 20 + BEAT_FRAMES - 1)?.wave).toBeGreaterThan(0);
    expect(beatAt(beats, 20 + BEAT_FRAMES)).toBeNull();
    expect(beatAt(beats, 56)?.index).toBe(1);
    expect(BEAT_FRAMES).toBeGreaterThanOrEqual(10);
    expect(BEAT_FRAMES).toBeLessThanOrEqual(14);
  });
});
