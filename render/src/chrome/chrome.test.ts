import { describe, expect, test } from "vitest";
import { CAPTION_MAX, CAPTION_ROW, captionLayout, captionSize, captionTokens, captionWord, lineWidth } from "./Captions";
import { CHAPTER_TOP, chapterBottom, chapterFit, chapterText } from "./ChapterLabel";
import { content, layout, safeWindow, visibleStageTop } from "../theme";
import { progressTicks } from "./Progress";

const single = { part: 1, total: 1, title: "L'oubli", label: "Partie" };
const series = { part: 2, total: 3, title: "Le sommeil", label: "Partie" };
const segments = [
  { from: 0, to: 90 },
  { from: 90, to: 300 },
  { from: 300, to: 360 },
];

describe("chrome", () => {
  test("un sous-titre n'affiche jamais de tiret cadratin", () => {
    expect(captionWord(`oui${String.fromCharCode(0x2014)}non`)).toBe("oui,non");
    expect(captionWord("mot")).toBe("mot");
  });

  test("le titre et le nom de la chaîne restent sous la barre d'état et les onglets de TikTok, hors des boutons de droite", () => {
    expect(CHAPTER_TOP).toBeGreaterThanOrEqual(240);
    expect(layout.marginTop).toBeGreaterThanOrEqual(240);
    expect(layout.marginSide).toBeGreaterThanOrEqual(safeWindow.left);
    expect(layout.width - layout.safeRight).toBeLessThanOrEqual(870);
    expect(layout.marginSide + 520).toBeLessThan(layout.width - layout.safeRight - 190);
  });

  test("les sous-titres et la barre de progression tiennent dans la zone sûre de TikTok", () => {
    const half = (content.width / 2) * layout.chromeScale;
    expect(layout.safeCenterX - half).toBeGreaterThanOrEqual(safeWindow.left - 10);
    expect(layout.safeCenterX + half).toBeLessThanOrEqual(safeWindow.right + 10);
  });

  test("une vidéo seule n'affiche que le titre", () => {
    expect(chapterText(single)).toBe("L'oubli");
    expect(chapterText(series)).toBe("Partie 2 · Le sommeil");
  });

  test("le titre de chapitre tient sur deux lignes au-dessus de la scène", () => {
    const long = { part: 8, total: 8, title: "Un titre beaucoup trop long qui ne tiendrait jamais sur une seule ligne du bandeau", label: "Partie" };
    const fit = chapterFit(long);
    expect(fit.lines.length).toBeLessThanOrEqual(2);
    expect(fit.size).toBeLessThan(38);
    expect(chapterBottom(long)).toBeLessThan(visibleStageTop);
    expect(chapterFit(single).size).toBe(38);
    expect(chapterBottom(series)).toBeLessThan(visibleStageTop);
  });

  test("une vidéo seule a un trait par segment", () => {
    const ticks = progressTicks(single, segments, 194, 360);
    expect(ticks.map((t) => t.weight)).toEqual([90, 210, 60]);
    expect(ticks[0].fill).toBe(1);
    expect(ticks[1].fill).toBeCloseTo(0.5, 2);
    expect(ticks[2].fill).toBe(0);
  });

  test("une partie d'une série n'affiche que sa propre barre", () => {
    const ticks = progressTicks(series, segments, 179.5, 360);
    expect(ticks).toHaveLength(1);
    expect(ticks[0].fill).toBeCloseTo(0.5, 2);
  });

  test("la dernière partie d'une série n'affiche aussi qu'une barre", () => {
    const last = { ...series, part: 3 };
    expect(progressTicks(last, segments, 0, 360)).toEqual([{ weight: 1, fill: 0 }]);
    expect(progressTicks(last, segments, 359, 360)).toEqual([{ weight: 1, fill: 1 }]);
  });
});

describe("sous-titres", () => {
  test("un groupe de deux mots tient sur une ligne, en très grand", () => {
    expect(captionSize(["cinq", "missiles"])).toBe(CAPTION_MAX);
    expect(captionSize(["Dis-moi", "pourquoi"])).toBeGreaterThanOrEqual(90);
    expect(captionLayout(["les", "États-Unis"]).lines).toHaveLength(1);
    expect(captionSize(["incompréhensiblement"])).toBeGreaterThanOrEqual(72);
  });

  test("un mot composé reste entier", () => {
    const { lines } = captionLayout(["Les", "États-Unis", "et", "l'Union"]);
    expect(lines.flat()).toEqual(["Les", "États-Unis", "et", "l'Union"]);
  });

  test("deux lignes équilibrées, jamais un mot seul quand il y en a quatre", () => {
    const words = ["extraordinairement", "incompréhensiblement", "mémorisables", "aujourd'hui"];
    const { size, lines } = captionLayout(words);
    expect(lines).toHaveLength(2);
    lines.forEach((line) => {
      expect(line.length).toBeGreaterThanOrEqual(2);
      expect(lineWidth(line, size)).toBeLessThanOrEqual(CAPTION_ROW);
    });
  });

  test("trois longs mots restent sur une ligne en réduisant avant de couper", () => {
    const { lines, size } = captionLayout(["Constantinople", "révolutionnaire", "soviétique"]);
    expect(lines.length === 1 || lines.every((l) => l.length >= 1)).toBe(true);
    lines.forEach((line) => expect(lineWidth(line, size)).toBeLessThanOrEqual(CAPTION_ROW));
  });
});

describe("ponctuation isolée", () => {
  test("un point d'interrogation seul rejoint le mot d'avant", () => {
    const tokens = captionTokens([
      { w: "bataille", from: 0, to: 5 },
      { w: "?", from: 5, to: 6 },
      { w: "Ça", from: 6, to: 9 },
    ]);
    expect(tokens.map((t) => t.w)).toEqual(["bataille ?", "Ça"]);
    expect(tokens[0].to).toBe(6);
  });
});
