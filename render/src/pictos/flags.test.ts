import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, test } from "vitest";
import { flagCode, FLAGS, REGION_FLAGS } from "./flags";

const flagDir = path.resolve(__dirname, "../../node_modules/flag-icons/flags/4x3");

describe("drapeaux", () => {
  test("liste triée de codes à deux lettres, avec eu, un et su", () => {
    expect([...FLAGS]).toEqual([...FLAGS].sort());
    expect(new Set(FLAGS).size).toBe(FLAGS.length);
    FLAGS.forEach((c) => expect(c).toMatch(/^[a-z]{2}$/));
    ["eu", "un", "su", "us", "cn", "ru", "in", "br", "za", "fr", "gb"].forEach((c) => expect(FLAGS).toContain(c));
  });

  test("chaque code ISO a son dessin, su est dessiné à part", () => {
    FLAGS.filter((c) => c !== "su").forEach((c) => expect(existsSync(path.join(flagDir, `${c}.svg`)), c).toBe(true));
    expect(existsSync(path.join(flagDir, "su.svg"))).toBe(false);
  });

  test("les drapeaux de régions ont leur dessin et sont reconnus", () => {
    expect([...REGION_FLAGS]).toEqual([...REGION_FLAGS].sort());
    ["gb-sct", "gb-eng", "gb-wls", "gb-nir", "es-ct"].forEach((c) => expect(REGION_FLAGS).toContain(c));
    REGION_FLAGS.forEach((c) => {
      expect(existsSync(path.join(flagDir, `${c}.svg`)), c).toBe(true);
      expect(flagCode(`flag:${c}`)).toBe(c);
    });
  });

  test("le paquet de drapeaux est sous licence MIT", () => {
    const pkg = JSON.parse(readFileSync(path.join(flagDir, "../../package.json"), "utf8"));
    expect(pkg.license).toBe("MIT");
  });

  test("flag:<code> est reconnu, le reste non", () => {
    expect(flagCode("flag:br")).toBe("br");
    expect(flagCode(" FLAG:CN ")).toBe("cn");
    expect(flagCode("flag:xx")).toBeNull();
    expect(flagCode("flag:gb-xx")).toBeNull();
    expect(flagCode("globe")).toBeNull();
  });
});
