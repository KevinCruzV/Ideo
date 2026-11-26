import { describe, expect, test } from "vitest";
import { chapterFit } from "../chrome/ChapterLabel";
import { layout } from "../theme";
import { FitOptions, fitText, splitKey, textWidth } from "./fit";

const SAMPLES = [
  "La lumière du soleil traverse des milliards de molécules dans le ciel bleu pendant toute la journée et rebondit partout autour de nous",
  "Pourquoi les avions ne volent jamais en ligne droite au-dessus de l'océan quand ils traversent la planète entière",
  "Le psychologue allemand Hermann Ebbinghaus a mesuré sa propre mémoire pendant plusieurs années consécutives",
];

const BOX_W = layout.contentRight - layout.contentLeft;
const BUBBLE_W = layout.contentRight - 360 - 68 + 36;
const ICON_W = BOX_W / 3 - 24;
const CHIP_ROOM = BOX_W - 46 - 28;
const LABEL_W = BOX_W - 160;

type Cap = { cap: number; fit: FitOptions; upper?: boolean };

const CAPS: Record<string, Cap> = {
  "key-title.accent": { cap: 40, fit: { maxWidth: BOX_W, maxLines: 2, max: 176, min: 64 } },
  "mascot.bubble": { cap: 80, fit: { maxWidth: BUBBLE_W, maxLines: 4, max: 74, min: 44 } },
  "fact-chips.chips": { cap: 28, fit: { maxWidth: CHIP_ROOM, maxLines: 2, max: 104, min: 44 } },
  "stack-list.items": { cap: 60, fit: { maxWidth: BOX_W - 104 - 30, maxLines: 3, max: 96, min: 56 } },
  "icon-grid.cells.label": { cap: 16, fit: { maxWidth: ICON_W, maxLines: 3, max: 52, min: 36 } },
  "shape-diagram.labels": { cap: 14, fit: { maxWidth: BOX_W / 2 - 16, maxLines: 2, max: 56, min: 44 } },
  "stamp.text": { cap: 48, fit: { maxWidth: BOX_W - 20 - 200, maxLines: 3, max: 136, min: 56 }, upper: true },
  "person-card.name": { cap: 48, fit: { maxWidth: BOX_W, maxLines: 2, max: 110, min: 60 } },
  "person-card.role": { cap: 100, fit: { maxWidth: BOX_W - 40, maxLines: 4, max: 62, min: 44 } },
  "artwork.title": { cap: 48, fit: { maxWidth: BOX_W, maxLines: 2, max: 96, min: 56 } },
  "artwork.artist": { cap: 40, fit: { maxWidth: BOX_W - 40, maxLines: 2, max: 60, min: 44 } },
  "counter.label": { cap: 60, fit: { maxWidth: BOX_W, maxLines: 3, max: 82, min: 56 } },
  "timeline.marks.at": { cap: 12, fit: { maxWidth: LABEL_W, maxLines: 1, max: 56, min: 44 } },
  "timeline.marks.label": { cap: 48, fit: { maxWidth: LABEL_W, maxLines: 2, max: 72, min: 48 } },
  "timeline.start": { cap: 30, fit: { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 44 } },
  "timeline.end": { cap: 30, fit: { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 44 } },
  "quote.text": { cap: 200, fit: { maxWidth: BOX_W, maxLines: 8, max: 80, min: 56 } },
  "quote.speaker": { cap: 32, fit: { maxWidth: BOX_W - 100, maxLines: 1, max: 54, min: 44 } },
  "object-state.states": { cap: 36, fit: { maxWidth: BOX_W, maxLines: 1, max: 72, min: 40 } },
  "versus.side": { cap: 24, fit: { maxWidth: (BOX_W - 56) / 2 - 10, maxLines: 2, max: 80, min: 48 } },
  "body.marks.label": { cap: 28, fit: { maxWidth: BOX_W * 0.46, maxLines: 3, max: 52, min: 44 } },
  "map.places.label": { cap: 24, fit: { maxWidth: 680, maxLines: 1, max: 52, min: 44 } },
  kicker: { cap: 28, fit: { maxWidth: BOX_W * 0.9, maxLines: 1, max: 38, min: 28 }, upper: true },
};

const SPLIT_CAPS: Record<string, { cap: number; head: FitOptions; key: FitOptions; tail: FitOptions }> = {
  hook: {
    cap: 60,
    head: { maxWidth: BOX_W - 20, maxLines: 3, max: 92, min: 56 },
    key: { maxWidth: BOX_W - 20, maxLines: 1, max: 170, min: 64 },
    tail: { maxWidth: BOX_W - 20, maxLines: 4, max: 84, min: 56 },
  },
  question: {
    cap: 60,
    head: { maxWidth: BOX_W - 20, maxLines: 3, max: 92, min: 56 },
    key: { maxWidth: BOX_W - 20, maxLines: 1, max: 170, min: 64 },
    tail: { maxWidth: BOX_W - 20, maxLines: 4, max: 84, min: 56 },
  },
  "key-title.text": {
    cap: 90,
    head: { maxWidth: BOX_W, maxLines: 4, max: 100, min: 56 },
    key: { maxWidth: BOX_W, maxLines: 2, max: 176, min: 64 },
    tail: { maxWidth: BOX_W, maxLines: 4, max: 100, min: 56 },
  },
};

const TITLE_CAP = 40;
const OUTRO_TAIL: FitOptions = { maxWidth: BOX_W - 30, maxLines: 2, max: 136, min: 60 };

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

describe("ponctuation détachée de l'accroche", () => {
  test("le « ? » final reste avec le mot-clé au lieu de partir seul", () => {
    const { before, key, after } = splitKey("Leclerc ou Aldi, qui vole le plus les Français ?");
    expect(key).toBe("Français ?");
    expect(after).toBe("");
    expect(before).toBe("Leclerc ou Aldi, qui vole le plus les");
  });

  test("le « ? » reste avec le dernier mot de la suite", () => {
    const { after } = splitKey("Dis-moi pourquoi le ciel est bleu ?", "pourquoi");
    expect(after).toBe("le ciel est bleu ?");
  });
});
