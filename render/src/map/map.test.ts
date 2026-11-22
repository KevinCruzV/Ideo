import { describe, expect, test } from "vitest";
import { FLAGS } from "../pictos/flags";
import { focusOf, placesOf, routeOf } from "../scenes/MapScene";
import { MAP_CODES, MAP_FOCUS } from "./codes";
import { COUNTRIES, VIEWS } from "./world";

describe("carte", () => {
  test("les codes sont triés, à deux lettres, tous des drapeaux, sans eu, un ni su", () => {
    expect([...MAP_CODES]).toEqual([...MAP_CODES].sort());
    MAP_CODES.forEach((c) => {
      expect(c).toMatch(/^[a-z]{2}$/);
      expect(FLAGS).toContain(c);
      expect(COUNTRIES[c]?.d.length).toBeGreaterThan(10);
    });
    ["eu", "un", "su"].forEach((c) => expect(MAP_CODES).not.toContain(c));
    ["cn", "kz", "ir", "tr", "it", "gl", "pa", "br", "ru", "in", "za", "us", "fr"].forEach((c) => expect(MAP_CODES).toContain(c));
  });

  test("les zones suivent le contrat et ont chacune un cadre", () => {
    expect([...MAP_FOCUS]).toEqual(["world", "europe", "africa", "asia", "north-america", "south-america", "middle-east", "oceania", "arctic"]);
    MAP_FOCUS.forEach((f) => expect(VIEWS[f]).toHaveLength(4));
  });

  test("les props mal formées sont filtrées", () => {
    expect(focusOf("lune")).toBe("world");
    expect(placesOf([{ code: "FR", label: "France" }, { code: "xx" }, "de"]).map((p) => p.code)).toEqual(["fr", "de"]);
    expect(routeOf(["cn", "zz", "it"])).toEqual(["cn", "it"]);
  });
});
