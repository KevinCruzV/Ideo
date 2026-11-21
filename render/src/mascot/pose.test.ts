import { describe, expect, test } from "vitest";
import { BLINK_FRAMES, blinkStarts, breath, gaze, HOP_FRAMES, hopLift, idleTilt, isBlinking, poseOf } from "./pose";
import { characterWidth, sizeForHead, VIEW } from "./Character";

describe("pose", () => {
  test("une pose inconnue retombe sur question", () => {
    expect(poseOf("danse")).toBe("question");
    expect(poseOf(undefined)).toBe("question");
    expect(poseOf(3)).toBe("question");
    expect(poseOf("")).toBe("question");
  });

  test("les poses connues passent, casse et espaces ignorés", () => {
    expect(poseOf("surprise")).toBe("surprise");
    expect(poseOf(" Montre ")).toBe("montre");
    expect(poseOf("CONTENT")).toBe("content");
  });
});

describe("clignement", () => {
  test("le calendrier est le même pour une même image", () => {
    const a = Array.from({ length: 600 }, (_, f) => isBlinking("mascot", f));
    const b = Array.from({ length: 600 }, (_, f) => isBlinking("mascot", f));
    expect(a).toEqual(b);
    expect(isBlinking("mascot", 250)).toBe(isBlinking("mascot", 250));
  });

  test("un clignement toutes les 3 à 4 secondes, dès la première", () => {
    const starts = blinkStarts("mascot", 900);
    expect(starts[0]).toBeLessThan(60);
    starts.slice(1).forEach((s, i) => {
      const gap = s - starts[i];
      expect(gap).toBeGreaterThanOrEqual(90);
      expect(gap).toBeLessThanOrEqual(120);
    });
    expect(starts.length).toBeGreaterThanOrEqual(8);
    expect(starts.length).toBeLessThanOrEqual(11);
  });

  test("les yeux restent fermés quelques images seulement", () => {
    const first = blinkStarts("mascot", 900)[0];
    expect(isBlinking("mascot", first - 1)).toBe(false);
    expect(isBlinking("mascot", first)).toBe(true);
    expect(isBlinking("mascot", first + BLINK_FRAMES - 1)).toBe(true);
    expect(isBlinking("mascot", first + BLINK_FRAMES)).toBe(false);
    expect(isBlinking("mascot", -5)).toBe(false);
  });

  test("une scène de 3 secondes cligne au moins une fois", () => {
    expect(Array.from({ length: 90 }, (_, f) => isBlinking("mascot", f)).some(Boolean)).toBe(true);
  });
});

describe("vie au repos", () => {
  test("la tête oscille en douceur dans deux degrés", () => {
    const tilts = Array.from({ length: 300 }, (_, f) => idleTilt("mascot", f));
    tilts.forEach((t) => expect(Math.abs(t)).toBeLessThanOrEqual(2));
    tilts.slice(1).forEach((t, i) => expect(Math.abs(t - tilts[i])).toBeLessThan(0.2));
    expect(Math.max(...tilts) - Math.min(...tilts)).toBeGreaterThan(1);
  });

  test("la respiration et le regard restent discrets", () => {
    Array.from({ length: 300 }, (_, f) => f).forEach((f) => {
      expect(Math.abs(breath(f) - 1)).toBeLessThanOrEqual(0.012);
      const [x, y] = gaze("mascot", f);
      expect(Math.abs(x)).toBeLessThanOrEqual(2);
      expect(Math.abs(y)).toBeLessThanOrEqual(1);
    });
  });

  test("le petit saut monte puis retombe à zéro", () => {
    expect(hopLift(9, 10)).toBe(0);
    const lifts = Array.from({ length: HOP_FRAMES + 6 }, (_, i) => hopLift(10 + i, 10));
    expect(Math.max(...lifts)).toBeGreaterThan(0.03);
    expect(lifts.slice(HOP_FRAMES)).toEqual(lifts.slice(HOP_FRAMES).map(() => 0));
    lifts.slice(1).forEach((l, i) => expect(Math.abs(l - lifts[i])).toBeLessThan(0.015));
  });

  test("la largeur suit la taille et la tête donne l'échelle", () => {
    expect(characterWidth(VIEW.h)).toBe(VIEW.w);
    expect(sizeForHead(66)).toBe(VIEW.h);
  });
});
