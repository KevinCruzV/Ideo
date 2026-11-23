import { describe, expect, it } from "vitest";
import { variantOf } from "./coerce";
import { COUNTER_VARIANTS } from "./Counter";
import { STAMP_VARIANTS } from "./Stamp";

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
