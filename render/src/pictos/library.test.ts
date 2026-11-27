import { describe, expect, test } from "vitest";
import { isPicto, pictoName, pictoPieces, PICTOS } from "./library";
import { turnAngle } from "./Picto";

const CONTRACT =
  "globe, flag, pin, city, house, factory, bank, coin, chart-up, chart-down, ship, plane, train, rocket, satellite, tank, shield, sword, bomb, dove, handshake, justice, wall, chain, lock, key, crown, ballot, megaphone, newspaper, tv, phone, computer, chip, book, brain, heart, eye, clock, calendar, lightbulb, atom, flask, leaf, sun, drop, fire, lightning, mountain, barrel, gear, people, lungs, stomach, spine, bone, muscle, tooth, blood, pill, syringe, virus, bed, pillow, moon, thermometer, scale-weight, apple, dumbbell, running-shoe, stethoscope, hospital, raised-bed, stomach-sleeper, knee-pillow, snore, pelvis-tilt, numb-arm, blood-stain, chalk-outline, crime-tape, handcuffs, knife, coffin, tombstone, mirror, mars, music-note, vinyl, microphone, ankle-monitor, hemicycle, credit-rating, constitution, broken-car, hourglass";

describe("pictos", () => {
  test("la bibliothèque a exactement les 96 noms du contrat", () => {
    expect([...PICTOS]).toEqual(CONTRACT.split(", "));
    expect(new Set(PICTOS).size).toBe(96);
  });

  test("chaque picto a des morceaux de papier dans la palette", () => {
    PICTOS.forEach((name) => {
      const pieces = pictoPieces(name);
      expect(pieces.length).toBeGreaterThan(0);
      pieces.forEach((p) => {
        expect(["red", "yellow", "blue", "ink", "cream"]).toContain(p.c);
        expect(p.d).not.toMatch(/NaN/);
      });
    });
  });

  test("seul le disque du vinyl tourne, autour de son centre, la pochette reste fixe", () => {
    const pieces = pictoPieces("vinyl");
    const turning = pieces.filter((p) => p.turn);
    expect(turning.length).toBeGreaterThanOrEqual(4);
    turning.forEach((p) => expect(p.turn).toEqual([60, 50]));
    expect(pieces.some((p) => !p.turn)).toBe(true);
    PICTOS.filter((name) => name !== "vinyl").forEach((name) => {
      pictoPieces(name).forEach((p) => expect(p.turn).toBeUndefined());
    });
  });

  test("le disque fait un tour en un peu moins de deux secondes", () => {
    expect(turnAngle(0, 30)).toBe(0);
    expect(turnAngle(30, 30)).toBeCloseTo(200);
    expect(turnAngle(15, 30)).toBeCloseTo(100);
  });

  test("un nom inconnu ne casse rien", () => {
    expect(isPicto("licorne")).toBe(false);
    expect(pictoName(undefined)).toBeNull();
    expect(pictoName(" Globe ")).toBe("globe");
  });
});
