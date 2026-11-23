import { describe, expect, it } from "vitest";
import { variantOf } from "./coerce";
import { COUNTER_VARIANTS } from "./Counter";
import { NOTE_PAPERS, STAMP_VARIANTS } from "./Stamp";
import { contrastPaper, pictoColors } from "../pictos/Picto";

describe("variants", () => {
  it("keeps any value inside the range", () => {
    expect(variantOf(undefined, 3)).toBe(0);
    expect(variantOf("x", 3)).toBe(0);
    expect(variantOf(4, 3)).toBe(1);
    expect(variantOf(-1, 3)).toBe(2);
    expect(variantOf(2, 0)).toBe(0);
  });

  it("offers three looks for stamp and counter, as the timeline expects", () => {
    expect(STAMP_VARIANTS.length).toBe(3);
    expect(COUNTER_VARIANTS).toBe(3);
  });
});

describe("note paper", () => {
  it("never takes a colour the drawing already uses", () => {
    expect(pictoColors("lock")).toContain("yellow");
    expect(contrastPaper("lock", NOTE_PAPERS)).not.toBe("yellow");
    for (const name of ["sun", "clock", "lock", "brain", "coin", "fire"]) {
      expect(pictoColors(name)).not.toContain(contrastPaper(name, NOTE_PAPERS));
    }
    expect(contrastPaper(undefined, NOTE_PAPERS)).toBe("yellow");
  });
});
