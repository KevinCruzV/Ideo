import { describe, expect, test } from "vitest";
import { numberIn } from "./Counter";

describe("compteur", () => {
  test("le chiffre est déjà visible à la première image, même quand le compte part de 0", () => {
    expect(numberIn(0)).toBeGreaterThan(0);
    expect(numberIn(0)).toBeLessThan(1);
  });

  test("le chiffre entre en fondu et est complet après quelques images", () => {
    expect(numberIn(-3)).toBe(0);
    expect(numberIn(1)).toBeGreaterThan(numberIn(0));
    expect(numberIn(3)).toBe(1);
    expect(numberIn(30)).toBe(1);
  });
});
