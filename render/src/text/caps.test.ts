import { describe, expect, test } from "vitest";
import { chapterFit } from "../chrome/ChapterLabel";
import { layout } from "../theme";
import { FitOptions, fitText, splitKey, textWidth } from "./fit";

const SAMPLES = [
  "La lumière du soleil traverse des milliards de molécules dans le ciel bleu pendant toute la journée et rebondit partout autour de nous",
  "Pourquoi les avions ne volent jamais en ligne droite au-dessus de l'océan quand ils traversent la planète entière",
  "Le psychologue allemand Hermann Ebbinghaus a mesuré sa propre mémoire pendant plusieurs années consécutives",
];

const BUBBLE_W = layout.width - layout.marginSide - 410 - 60;
const ICON_W = (layout.width - 96) / 3 - 24;
const CHIP_ROOM = 700;

type Cap = { cap: number; fit: FitOptions; upper?: boolean };

const CAPS: Record<string, Cap> = {
  "key-title.accent": { cap: 40, fit: { maxWidth: 920, maxLines: 2, max: 170, min: 64 } },
  "mascot.bubble": { cap: 80, fit: { maxWidth: BUBBLE_W, maxLines: 4, max: 72, min: 44 } },
  "fact-chips.chips": { cap: 28, fit: { maxWidth: CHIP_ROOM, maxLines: 1, max: 60, min: 44 } },
  "stack-list.items": { cap: 60, fit: { maxWidth: 790, maxLines: 2, max: 64, min: 44 } },
  "icon-grid.cells.label": { cap: 16, fit: { maxWidth: ICON_W, maxLines: 2, max: 50, min: 40 } },
  "shape-diagram.labels": { cap: 14, fit: { maxWidth: 320, maxLines: 2, max: 60, min: 48 } },
  "stamp.text": { cap: 48, fit: { maxWidth: 700, maxLines: 3, max: 150, min: 56 }, upper: true },
  "person-card.name": { cap: 48, fit: { maxWidth: 900, maxLines: 2, max: 104, min: 56 } },
  "person-card.role": { cap: 100, fit: { maxWidth: 860, maxLines: 3, max: 58, min: 44 } },
  "counter.label": { cap: 60, fit: { maxWidth: 900, maxLines: 2, max: 76, min: 48 } },
  "timeline.marks.at": { cap: 12, fit: { maxWidth: 800, maxLines: 2, max: 52, min: 44 } },
  "timeline.marks.label": { cap: 48, fit: { maxWidth: 800, maxLines: 2, max: 52, min: 44 } },
  "timeline.start": { cap: 30, fit: { maxWidth: 760, maxLines: 1, max: 64, min: 44 } },
  "timeline.end": { cap: 30, fit: { maxWidth: 760, maxLines: 1, max: 64, min: 44 } },
  "quote.text": { cap: 200, fit: { maxWidth: 920, maxLines: 6, max: 84, min: 46 } },
  "quote.speaker": { cap: 32, fit: { maxWidth: 760, maxLines: 1, max: 56, min: 40 } },
  "object-state.states": { cap: 36, fit: { maxWidth: 900, maxLines: 1, max: 72, min: 44 } },
};

const SPLIT_CAPS: Record<string, { cap: number; head: FitOptions; key: FitOptions; tail: FitOptions }> = {
  hook: {
    cap: 60,
    head: { maxWidth: 900, maxLines: 2, max: 80, min: 52 },
    key: { maxWidth: 900, maxLines: 1, max: 160, min: 64 },
    tail: { maxWidth: 900, maxLines: 3, max: 72, min: 48 },
  },
  "key-title.text": {
    cap: 90,
    head: { maxWidth: 920, maxLines: 3, max: 96, min: 52 },
    key: { maxWidth: 920, maxLines: 2, max: 170, min: 64 },
    tail: { maxWidth: 920, maxLines: 3, max: 96, min: 52 },
  },
};

const TITLE_CAP = 40;
const OUTRO_TAIL: FitOptions = { maxWidth: 900, maxLines: 2, max: 130, min: 60 };

const sized = (sample: string, n: number): string => {
  let text = "";
  while (text.length < n) text += (text ? " " : "") + sample;
  return text.slice(0, n).replace(/ $/, "e");
};

const fits = (text: string, options: FitOptions): boolean => {
  if (!text) return true;
  const fit = fitText(text, options);
  return (
    fit.lines.length <= options.maxLines &&
    fit.lines.every((line) => !line.includes("…") && textWidth(line, fit.size) <= options.maxWidth)
  );
};

const lengths = (cap: number) => Array.from({ length: cap }, (_, i) => i + 1);

describe("plafonds de texte à l'écran", () => {
  test.each(Object.entries(CAPS))("%s tient sans coupure jusqu'au plafond", (_, { cap, fit, upper }) => {
    for (const sample of SAMPLES) {
      for (const n of lengths(cap)) {
        const text = upper ? sized(sample, n).toUpperCase() : sized(sample, n);
        expect(fits(text, fit), text).toBe(true);
      }
    }
  });

  test.each(Object.entries(SPLIT_CAPS))("%s tient avec le mot-clé au début, à la fin ou choisi seul", (_, spec) => {
    for (const sample of SAMPLES) {
      for (const n of lengths(spec.cap)) {
        const text = sized(sample, n);
        const words = text.split(" ");
        for (const accent of [words[0], words[words.length - 1], undefined]) {
          const { before, key, after } = splitKey(text, accent);
          expect(fits(before, spec.head) && fits(key, spec.key) && fits(after, spec.tail), `${text} / ${accent}`).toBe(true);
        }
      }
    }
  });

  test("le titre tient dans le bandeau et dans la fin de vidéo", () => {
    for (const sample of SAMPLES) {
      for (const n of lengths(TITLE_CAP)) {
        const title = sized(sample, n);
        const fit = chapterFit({ part: 8, total: 8, title, label: "Partie" });
        expect(fit.lines.every((line) => !line.includes("…")), title).toBe(true);
        expect(fits(title, OUTRO_TAIL), title).toBe(true);
      }
    }
  });

  test("un caractère chinois ou japonais compte pour un cadratin", () => {
    expect(textWidth("空気", 100)).toBe(200);
    expect(textWidth("ａ", 100)).toBe(100);
  });
});
