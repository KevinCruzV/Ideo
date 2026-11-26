import { describe, expect, test } from "vitest";
import type { Segment } from "../types";
import { paperOf, supportsFor } from "./supports";

const seg = (kind: Segment["kind"], type?: string, props: Record<string, unknown> = {}): Segment => ({ kind, type, from: 0, to: 30, props });
const scene = (type: string, props: Record<string, unknown> = {}) => seg("scene", type, props);

describe("support de chaque scène", () => {
  test("un prix va sur un ticket, un pourcentage sur la matière", () => {
    const s = supportsFor([seg("hook"), scene("stamp"), scene("counter", { unit: "€" }), scene("fact-chips"), scene("counter", { unit: "cts" }), scene("fact-chips"), scene("counter", { unit: "%" }), scene("shape-diagram", { unit: "€" }), seg("outro")], "kraft");
    expect(s).toEqual(["kraft", "none", "ticket", "kraft", "ticket", "kraft", "kraft", "ticket", "kraft"]);
  });

  test("citation et frise sur une coupure, phrase-clé sur un post-it sauf la première scène", () => {
    const s = supportsFor([seg("hook"), scene("key-title"), scene("quote"), scene("stack-list"), scene("timeline"), scene("key-title"), scene("mascot")], "creme");
    expect(s).toEqual(["creme", "creme", "clipping", "creme", "clipping", "postit", "none"]);
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
