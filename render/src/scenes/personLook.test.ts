import { describe, expect, test } from "vitest";
import persons from "../../fixtures/persons.json";
import { AGES, FACIALS, GENDERS, HAIR_COLORS, HAIRS, HATS, JOB_HATS, JOBS, lookOf, NEUTRAL_LOOK, OUTFITS, SKINS } from "./personLook";

describe("personnages", () => {
  test("les valeurs suivent le contrat", () => {
    expect([...HAIRS]).toEqual(["none", "short", "side", "long", "curly", "wild", "bun", "crown-bald"]);
    expect([...HAIR_COLORS]).toEqual(["black", "brown", "blond", "red", "grey", "white"]);
    expect([...FACIALS]).toEqual(["none", "moustache", "beard", "goatee", "sideburns"]);
    expect([...HATS]).toEqual(["none", "cap", "kepi", "bicorne", "crown", "helmet", "top-hat", "beret", "turban", "laurel", "wig"]);
    expect([...OUTFITS]).toEqual(["suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress"]);
    expect([...SKINS]).toEqual(["light", "tan", "brown", "dark"]);
    expect([...GENDERS]).toEqual(["woman", "man"]);
    expect([...AGES]).toEqual(["child", "adult", "old"]);
    expect([...JOBS]).toEqual(["police", "firefighter", "doctor", "judge", "soldier", "worker", "journalist", "lawyer"]);
  });

  test("un métier donne sa tenue et son couvre-chef, une tenue ou un chapeau explicite les remplace", () => {
    expect(lookOf({ job: "police" })).toMatchObject({ outfit: "police", hat: "police-cap" });
    expect(lookOf({ job: "firefighter" }).hat).toBe("fire-helmet");
    expect(lookOf({ job: "worker" }).hat).toBe("hard-hat");
    expect(lookOf({ job: "soldier" }).hat).toBe("army-helmet");
    expect(lookOf({ job: "judge" })).toMatchObject({ outfit: "judge", hat: "none" });
    expect(lookOf({ job: "police", outfit: "suit", hat: "beret" })).toMatchObject({ outfit: "suit", hat: "beret" });
    JOBS.forEach((job) => expect(lookOf({ job }).outfit).toBe(job));
    expect(JOB_HATS.length).toBe(4);
  });

  test("une femme et un homme se dessinent différemment, l'âge change les cheveux et le visage", () => {
    const woman = lookOf({ gender: "woman" });
    expect(woman).toMatchObject({ gender: "woman", hair: "long", outfit: "dress", facial: "none" });
    expect(lookOf({ gender: "woman", facial: "beard" }).facial).toBe("none");
    expect(lookOf({ gender: "man" })).toMatchObject({ gender: "man", hair: "short", outfit: "suit" });
    expect(lookOf({ age: "old" }).hairColor).toBe("grey");
    expect(lookOf({ age: "child", facial: "beard" }).facial).toBe("none");
    expect(lookOf({ gender: "ogre", age: "ancient", job: "mage" })).toEqual(NEUTRAL_LOOK);
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
    GENDERS.forEach((v) => expect(seen("gender").has(v), v).toBe(true));
    AGES.forEach((v) => expect(seen("age").has(v), v).toBe(true));
    JOBS.forEach((v) => expect(seen("outfit").has(v), v).toBe(true));
    JOB_HATS.forEach((v) => expect(seen("hat").has(v), v).toBe(true));
    expect(seen("glasses").has("true")).toBe(true);
    expect(persons.length).toBeGreaterThanOrEqual(12);
  });
});
