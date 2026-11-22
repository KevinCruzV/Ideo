import { describe, expect, test } from "vitest";
import persons from "../../fixtures/persons.json";
import { FACIALS, HAIR_COLORS, HAIRS, HATS, lookOf, NEUTRAL_LOOK, OUTFITS, SKINS } from "./personLook";

describe("personnages", () => {
  test("les valeurs suivent le contrat", () => {
    expect([...HAIRS]).toEqual(["none", "short", "side", "long", "curly", "wild", "bun", "crown-bald"]);
    expect([...HAIR_COLORS]).toEqual(["black", "brown", "blond", "red", "grey", "white"]);
    expect([...FACIALS]).toEqual(["none", "moustache", "beard", "goatee", "sideburns"]);
    expect([...HATS]).toEqual(["none", "cap", "kepi", "bicorne", "crown", "helmet", "top-hat", "beret", "turban", "laurel", "wig"]);
    expect([...OUTFITS]).toEqual(["suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress"]);
    expect([...SKINS]).toEqual(["light", "tan", "brown", "dark"]);
  });

  test("sans attribut, le personnage neutre ; une valeur inconnue retombe sur le neutre", () => {
    expect(lookOf({})).toEqual(NEUTRAL_LOOK);
    expect(lookOf({ hat: "sombrero", outfit: 3 }).hat).toBe("none");
    expect(lookOf({ glasses: "true" }).glasses).toBe(true);
  });

  test("la fixture de contrôle couvre chaque valeur de chaque attribut", () => {
    const looks = persons.map((p) => lookOf(p));
    const seen = (key: keyof (typeof looks)[number]) => new Set(looks.map((l) => String(l[key])));
    HAIRS.forEach((v) => expect(seen("hair").has(v), v).toBe(true));
    HAIR_COLORS.forEach((v) => expect(seen("hairColor").has(v), v).toBe(true));
    FACIALS.forEach((v) => expect(seen("facial").has(v), v).toBe(true));
    HATS.filter((v) => v !== "none").forEach((v) => expect(seen("hat").has(v), v).toBe(true));
    OUTFITS.forEach((v) => expect(seen("outfit").has(v), v).toBe(true));
    SKINS.forEach((v) => expect(seen("skin").has(v), v).toBe(true));
    expect(seen("glasses").has("true")).toBe(true);
    expect(persons.length).toBeGreaterThanOrEqual(12);
  });
});
