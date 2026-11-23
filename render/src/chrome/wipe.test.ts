import { describe, expect, test } from "vitest";
import { inside, WIPE_BEFORE, WIPE_FRAMES, WIPE_KINDS, wipeKind, wipeOffset, wipePieces } from "./Wipe";

const POINTS: [number, number][] = [[0, 0], [1079, 0], [0, 1919], [1079, 1919], [540, 960], [540, 0], [540, 1919], [0, 960], [1079, 960], [270, 480], [810, 1440], [540, 1000], [540, 920]];

const covered = (kind: (typeof WIPE_KINDS)[number], frame: number, x: number, y: number) => wipePieces(kind, frame).some((p) => inside(p.pts, x, y));

describe("transitions visuelles", () => {
  test("chaque effet couvre tout l'écran à l'image de la coupure", () => {
    WIPE_KINDS.forEach((kind) => POINTS.forEach(([x, y]) => expect(covered(kind, WIPE_BEFORE, x, y), `${kind} ${x},${y}`).toBe(true)));
  });

  test("chaque effet laisse l'écran libre au début et à la fin", () => {
    WIPE_KINDS.forEach((kind) => {
      [0, WIPE_FRAMES].forEach((frame) => POINTS.forEach(([x, y]) => expect(covered(kind, frame, x, y), `${kind} ${frame} ${x},${y}`).toBe(false)));
    });
  });

  test("le glissement garde son mouvement d'origine", () => {
    expect(wipeOffset(WIPE_BEFORE)).toBeCloseTo(0, 5);
    expect(wipeOffset(0)).toBeGreaterThan(1000);
    expect(wipeOffset(WIPE_FRAMES)).toBeLessThan(-1000);
  });

  test("le choix est déterministe, ne répète jamais le précédent et montre tous les effets", () => {
    const first = Array.from({ length: 60 }, (_, i) => wipeKind(i));
    expect(Array.from({ length: 60 }, (_, i) => wipeKind(i))).toEqual(first);
    first.slice(1).forEach((kind, i) => expect(kind).not.toBe(first[i]));
    expect(new Set(first.slice(0, 12)).size).toBe(WIPE_KINDS.length);
    expect(WIPE_KINDS.length).toBeGreaterThanOrEqual(4);
  });
});
