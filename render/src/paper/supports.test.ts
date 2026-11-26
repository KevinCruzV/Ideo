import { describe, expect, test } from "vitest";
import type { Segment } from "../types";
import { PAPER_COLORS } from "../theme";
import { paperOf, photoFrame, supportsFor } from "./supports";

const seg = (kind: Segment["kind"], type?: string, props: Record<string, unknown> = {}): Segment => ({ kind, type, from: 0, to: 30, props });
const scene = (type: string, props: Record<string, unknown> = {}) => seg("scene", type, props);

describe("support de chaque scène", () => {
  test("un prix va sur un ticket, un pourcentage sur la matière", () => {
    const s = supportsFor([seg("hook"), scene("stamp"), scene("counter", { unit: "€" }), scene("fact-chips"), scene("counter", { unit: "cts" }), scene("fact-chips"), scene("counter", { unit: "%" }), scene("shape-diagram", { unit: "€" }), seg("outro")], "kraft");
    expect(s).toEqual(["kraft", "none", "ticket", "kraft", "ticket", "kraft", "kraft", "ticket", "kraft"]);
  });

  test("citation et frise sur une coupure, phrase-clé sur un post-it sauf la première scène", () => {
    const s = supportsFor([seg("hook"), scene("key-title"), scene("quote"), scene("stack-list"), scene("timeline"), scene("key-title"), scene("mascot")], "creme");
    expect(s).toEqual(["creme", "creme", "clipping", "creme", "clipping", "postit", "creme"]);
  });

  test("jamais deux fois de suite le même support spécial", () => {
    expect(supportsFor([scene("fact-chips"), scene("stamp"), scene("stamp"), scene("quote"), scene("quote")], "album")).toEqual(["album", "none", "album", "clipping", "album"]);
  });

  test("matière par défaut", () => {
    expect(paperOf("carton", false)).toBe("creme");
    expect(paperOf(undefined, false)).toBe("creme");
    expect(paperOf(undefined, true)).toBe("journal");
    expect(paperOf("kraft", true)).toBe("kraft");
  });
});

const channel = (hex: string, i: number) => {
  const v = parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16) / 255;
  return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
};
const luminance = (hex: string) => 0.2126 * channel(hex, 0) + 0.7152 * channel(hex, 1) + 0.0722 * channel(hex, 2);
const ratio = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

describe("couleurs des supports", () => {
  test("le texte encre reste lisible sur chaque support, en clair et en sombre", () => {
    for (const mode of ["light", "dark"] as const) {
      for (const [support, { fill, ink }] of Object.entries(PAPER_COLORS[mode])) {
        expect(ratio(fill, ink), `${mode} ${support}`).toBeGreaterThanOrEqual(4.5);
      }
    }
  });
});

describe("cadre des photos", () => {
  test("polaroïd dans un album, cadre découpé ailleurs", () => {
    expect(photoFrame("album")).toBe("polaroid");
    for (const paper of ["creme", "kraft", "journal", "millimetre"] as const) expect(photoFrame(paper)).toBe("plain");
  });
});
