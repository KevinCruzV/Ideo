import { describe, expect, it } from "vitest";
import { coverAccent, partTag } from "./Cover";
import { accentCycle } from "./theme";

describe("cover", () => {
  it("gives the same accent to the same title and a known accent to any title", () => {
    expect(coverAccent("The speed of light nobody measured")).toBe(coverAccent("The speed of light nobody measured"));
    for (const title of ["a", "Pourquoi le ciel est bleu", "Quel pays domine le monde", ""]) {
      expect(accentCycle).toContain(coverAccent(title));
    }
  });

  it("varies the accent across titles", () => {
    const titles = ["Pourquoi le ciel est bleu", "Quel pays domine le monde", "Le meurtrier qui a menti", "Ta position de sommeil", "The speed of light nobody measured", "Les villes vides"];
    expect(new Set(titles.map(coverAccent)).size).toBeGreaterThan(1);
  });

  it("shows the part tag only for a series", () => {
    expect(partTag("Partie", 1, 1)).toBeNull();
    expect(partTag("Partie", 2, 3)).toBe("Partie 2/3");
  });
});
