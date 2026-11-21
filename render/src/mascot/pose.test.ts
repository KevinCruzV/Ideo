import { describe, expect, test } from "vitest";
import { BLINK_FRAMES, blinkStarts, hopLift, idleTilt, isBlinking, poseOf } from "./pose";
import { characterWidth } from "./Character";

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
  test("la tête change de un ou deux degrés, par paliers de plusieurs pas", () => {
    const tilts = Array.from({ length: 300 }, (_, f) => idleTilt("mascot", f));
    tilts.forEach((t) => {
      expect(Number.isInteger(t)).toBe(true);
      expect(Math.abs(t)).toBeLessThanOrEqual(2);
    });
    const changes = tilts.filter((t, i) => i > 0 && t !== tilts[i - 1]).length;
    expect(changes).toBeGreaterThan(2);
    expect(changes).toBeLessThan(300 / 10);
    expect(idleTilt("mascot", 3)).toBe(idleTilt("mascot", 4));
  });

  test("le saut à l'arrivée de la bulle dure deux pas puis s'arrête", () => {
    expect(hopLift(9, 10)).toBe(0);
    const lifts = [10, 11, 12, 13, 14, 15, 16, 40].map((f) => hopLift(f, 10));
    expect(lifts.slice(0, 5).every((l) => l > 0)).toBe(true);
    expect(lifts[0]).toBeGreaterThan(lifts[4]);
    expect(lifts.slice(5)).toEqual([0, 0, 0]);
  });

  test("la largeur suit la taille", () => {
    expect(characterWidth(152)).toBe(142);
  });
});
