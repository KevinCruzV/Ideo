import { describe, expect, test } from "vitest";
import { accentAt, accentForIndex, colors, dimmed, moodOf, onPaper, palettes, PaperColor, segmentAccent, setMood, shade } from "./theme";

describe("accent", () => {
  test("rotation rouge, jaune, bleu par index de segment", () => {
    expect([0, 1, 2, 3, 4, 13].map(accentForIndex)).toEqual(["red", "yellow", "blue", "red", "yellow", "yellow"]);
    expect(accentForIndex(Number.NaN)).toBe("red");
  });

  test("accentAt suit le segment courant", () => {
    const spans = [
      { from: 0, to: 10, accent: accentForIndex(0) },
      { from: 10, to: 20, accent: accentForIndex(1) },
    ];
    expect(accentAt(spans, 5)).toBe("red");
    expect(accentAt(spans, 12)).toBe("yellow");
    expect(accentAt(spans, 99)).toBe("red");
  });

  test("une scène mascotte ne prend jamais le bleu, réservé au buste", () => {
    expect(segmentAccent(2, "mascot")).toBe("red");
    expect(segmentAccent(5, "mascot")).toBe("red");
    expect(segmentAccent(1, "mascot")).toBe("yellow");
    expect(segmentAccent(0, "mascot")).toBe("red");
    expect(segmentAccent(2, "key-title")).toBe("blue");
    expect(segmentAccent(2)).toBe("blue");
  });
});

const luminance = (hex: string): number => {
  const channel = (i: number) => {
    const v = parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16) / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(0) + 0.7152 * channel(1) + 0.0722 * channel(2);
};

const ratio = (a: string, b: string): number => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

describe("humeur sombre", () => {
  const papers: PaperColor[] = ["red", "yellow", "blue", "cream", "ink"];

  test("seule la valeur dark est reconnue", () => {
    expect(moodOf("dark")).toBe("dark");
    expect(moodOf("light")).toBeUndefined();
    expect(moodOf(undefined)).toBeUndefined();
  });

  test("le texte sur chaque papier a un contraste d'au moins 4,5", () => {
    for (const paper of papers) {
      expect(ratio(palettes.dark.colors[paper], palettes.dark.onPaper[paper])).toBeGreaterThanOrEqual(4.5);
    }
  });

  test("le texte posé sur le fond (titre de chapitre, sous-titres, progression) est lisible", () => {
    expect(ratio(palettes.dark.colors.fg, palettes.dark.colors.background)).toBeGreaterThanOrEqual(7);
    expect(ratio(palettes.light.colors.fg, palettes.light.colors.background)).toBeGreaterThanOrEqual(7);
  });

  test("les mots à venir des sous-titres restent lisibles sur le fond sombre", () => {
    const mixChannel = (a: string, b: string, t: number, i: number) => Math.round(parseInt(a.slice(1 + i * 2, 3 + i * 2), 16) * (1 - t) + parseInt(b.slice(1 + i * 2, 3 + i * 2), 16) * t);
    setMood("dark");
    const t = dimmed;
    const hex = [0, 1, 2].map((i) => mixChannel(colors.background, colors.fg, t, i).toString(16).padStart(2, "0")).join("");
    expect(ratio(`#${hex}`, colors.background)).toBeGreaterThanOrEqual(4.5);
    setMood(undefined);
  });

  test("les papiers se détachent du fond", () => {
    for (const paper of papers) {
      expect(ratio(palettes.dark.colors[paper], palettes.dark.colors.background)).toBeGreaterThanOrEqual(1.25);
    }
  });

  test("le fond est vraiment sombre et setMood change puis rétablit la palette", () => {
    expect(luminance(palettes.dark.colors.background)).toBeLessThan(0.05);
    setMood("dark");
    expect(colors.background).toBe(palettes.dark.colors.background);
    expect(onPaper.yellow).toBe(palettes.dark.onPaper.yellow);
    expect(shade).toBe(palettes.dark.shade);
    setMood(undefined);
    expect(colors.background).toBe(palettes.light.colors.background);
    expect(shade).toBe(palettes.light.shade);
  });
});
