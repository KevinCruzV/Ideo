import { describe, expect, it } from "vitest";
import { artKind, coverAccent, coverHeadFit, coverLayout, coverSheetHeight, coverText, DISK, PHOTO_SCALE, partTag, splitHook } from "./Cover";
import { PHOTO_H } from "./scenes/PhotoFrame";
import { accentCycle } from "./theme";

describe("cover", () => {
  it("gives the same accent to the same title and a known accent to any title", () => {
    expect(coverAccent("The speed of light nobody measured")).toBe(coverAccent("The speed of light nobody measured"));
    for (const title of ["a", "Pourquoi le ciel est bleu", "Quel pays domine le monde", ""]) {
      expect(accentCycle).toContain(coverAccent(title));
    }
  });

  it("varies the accent across titles", () => {
    const titles = ["Pourquoi le ciel est bleu", "Quel pays domine le monde", "Le meurtrier qui a menti", "Ta position de sommeil", "The speed of light nobody measured", "Les villes vides"];
    expect(new Set(titles.map(coverAccent)).size).toBeGreaterThan(1);
  });

  it("shows the part tag only for a series", () => {
    expect(partTag("Partie", 1, 1)).toBeNull();
    expect(partTag("Partie", 2, 3)).toBe("Partie 2/3");
  });

  it("shows the photo of the person when the cover has one, else the picto, else the mascot", () => {
    expect(artKind("photo.jpg", "sun")).toBe("photo");
    expect(artKind("photo-marie-curie.png", null)).toBe("photo");
    expect(artKind(undefined, "sun")).toBe("picto");
    expect(artKind("../photo.jpg", "sun")).toBe("picto");
    expect(artKind(null, null)).toBe("mascot");
  });

  it("draws the main person's face when the cover has no photo but a person-card look", () => {
    expect(artKind(undefined, "sun", { name: "Marie Curie" })).toBe("bust");
    expect(artKind(undefined, null, { name: "Marie Curie" })).toBe("bust");
    expect(artKind("photo.jpg", null, { name: "Marie Curie" })).toBe("photo");
    expect(artKind(undefined, "sun", null)).toBe("picto");
  });

  it("scales the photo frame to the height of the disk", () => {
    expect(PHOTO_H * PHOTO_SCALE).toBeCloseTo(DISK, 0);
  });

  it("keeps the longest title and the art inside the 3:4 crop of the profile grid", () => {
    const head = coverHeadFit("Pourquoi 1,5 milliard de personnes dorment mal la nuit ?");
    expect(head.lines.join(" ")).not.toContain("…");
    const { sheetY, artTop } = coverLayout(coverSheetHeight(head.lines.length, head.size), DISK);
    expect(sheetY).toBeGreaterThanOrEqual(240);
    expect(artTop + DISK).toBeLessThanOrEqual(1920 - 240);
  });

  it("splits the hook at its first comma or colon into a big title and a smaller line", () => {
    expect(splitHook("L'histoire de Marvin Gaye, partie 1 : de l'église à Motown")).toEqual({
      head: "L'histoire de Marvin Gaye",
      sub: "partie 1 : de l'église à Motown",
    });
    expect(splitHook("Marvin Gaye : la chute, la fin")).toEqual({ head: "Marvin Gaye", sub: "la chute, la fin" });
  });

  it("keeps a hook without separator whole and never cuts inside a number", () => {
    expect(splitHook("Dis-moi pourquoi le ciel est bleu ?")).toEqual({ head: "Dis-moi pourquoi le ciel est bleu ?", sub: null });
    expect(splitHook("Pourquoi 1,5 milliard de personnes dorment mal ?")).toEqual({
      head: "Pourquoi 1,5 milliard de personnes dorment mal ?",
      sub: null,
    });
    expect(splitHook("Pourquoi, ")).toEqual({ head: "Pourquoi,", sub: null });
    expect(splitHook("")).toEqual({ head: "", sub: null });
  });

  it("puts a single big title on the cover, the hook split in two, without repeating the video title", () => {
    expect(coverText("Marvin Gaye : de l'église à Motown", "L'histoire de Marvin Gaye, partie 1 : de l'église à Motown", 1, 2, "Partie")).toEqual({
      head: "L'histoire de Marvin Gaye",
      sub: "partie 1 : de l'église à Motown",
      tag: null,
    });
  });

  it("keeps the part tag when the hook does not name the part, and falls back on the title without hook", () => {
    expect(coverText("Le ciel", "Dis-moi pourquoi le ciel est bleu ?", 2, 3, "Partie")).toEqual({
      head: "Dis-moi pourquoi le ciel est bleu ?",
      sub: null,
      tag: "Partie 2/3",
    });
    expect(coverText("Le ciel", "", 1, 1, "Partie")).toEqual({ head: "Le ciel", sub: null, tag: null });
    expect(coverText("Le ciel", undefined, 1, 2, "Part")).toEqual({ head: "Le ciel", sub: null, tag: "Part 1/2" });
  });
});
