import { describe, expect, test } from "vitest";
import { isPicto, pictoName, pictoPieces, PICTOS } from "./library";

const CONTRACT =
  "globe, flag, pin, city, house, factory, bank, coin, chart-up, chart-down, ship, plane, train, rocket, satellite, tank, shield, sword, bomb, dove, handshake, justice, wall, chain, lock, key, crown, ballot, megaphone, newspaper, tv, phone, computer, chip, book, brain, heart, eye, clock, calendar, lightbulb, atom, flask, leaf, sun, drop, fire, lightning, mountain, barrel, gear, people, lungs, stomach, spine, bone, muscle, tooth, blood, pill, syringe, virus, bed, pillow, moon, thermometer, scale-weight, apple, dumbbell, running-shoe, stethoscope, hospital, raised-bed, stomach-sleeper, knee-pillow, snore, pelvis-tilt, numb-arm";

describe("pictos", () => {
  test("la bibliothèque a exactement les 78 noms du contrat", () => {
    expect([...PICTOS]).toEqual(CONTRACT.split(", "));
    expect(new Set(PICTOS).size).toBe(78);
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

  test("un nom inconnu ne casse rien", () => {
    expect(isPicto("licorne")).toBe(false);
    expect(pictoName(undefined)).toBeNull();
    expect(pictoName(" Globe ")).toBe("globe");
  });
});
