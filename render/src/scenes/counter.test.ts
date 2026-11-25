import { describe, expect, test } from "vitest";
import { numberIn } from "./Counter";

describe("compteur", () => {
  test("le chiffre de départ est visible dès la première image, même quand le compte part de 0", () => {
    expect(numberIn(0)).toBe(1);
    expect(numberIn(1)).toBe(1);
    expect(numberIn(30)).toBe(1);
  });
});
