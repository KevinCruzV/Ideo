import { describe, expect, test } from "vitest";
import { BODY_PARTS, BODY_POSES, BODY_SETTINGS, BODY_TONES, bodyPose, bodySetting, bodyTone } from "./bodyOptions";
import { anchorOf, rigOf } from "./bodyRig";
import { marksOf } from "./BodyScene";

describe("scène body", () => {
  test("les valeurs suivent le contrat", () => {
    expect([...BODY_POSES]).toEqual(["standing", "sitting", "walking", "running", "lying-back", "lying-starfish", "lying-side-left", "lying-side-right", "lying-fetal", "lying-stomach"]);
    expect([...BODY_SETTINGS]).toEqual(["none", "bed", "chair", "desk", "outdoor"]);
    expect([...BODY_PARTS]).toEqual(["head", "brain", "neck", "throat", "shoulders", "chest", "heart", "lungs", "stomach", "back", "spine", "hips", "arms", "hands", "knees", "legs", "feet"]);
    expect([...BODY_TONES]).toEqual(["good", "bad", "neutral"]);
  });

  test("valeurs inconnues : repli sûr", () => {
    expect(bodyPose("danse")).toBe("standing");
    expect(bodySetting(undefined)).toBe("none");
    expect(bodyTone("super")).toBe("neutral");
    expect(marksOf([{ part: "heart", label: "Cœur" }, { part: "aile" }, "knees", 1, 2, 3]).map((m) => m.part)).toEqual(["heart", "knees"]);
  });

  test("chaque zone a un point d'ancrage dans chaque posture", () => {
    BODY_POSES.forEach((pose) => {
      const rig = rigOf(pose);
      BODY_PARTS.forEach((part) => {
        const a = anchorOf(rig, part);
        expect(Number.isFinite(a.at[0]) && Number.isFinite(a.at[1])).toBe(true);
        expect(a.at[0]).toBeGreaterThan(0);
        expect(a.at[0]).toBeLessThan(400);
      });
    });
  });
});
