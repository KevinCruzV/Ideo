import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { cutEdge } from "../paper/motion";
import { colors, content, fonts, layout, shade } from "../theme";
import { textWidth } from "../text/fit";
import { str } from "../scenes/coerce";
import { CaptionGroup } from "../types";

export const CAPTION_MAX = 104;
export const CAPTION_MIN = 60;
export const CAPTION_ONE_LINE_MIN = 80;
export const CAPTION_ROW = content.width - 60;
export const CAPTION_LINE = 1.15;
export const CAPTION_TWO_LINE_MAX = 84;
const PAD = 0.14;
const GAP = 0.04;
const LABEL_PAD_Y = 0.14;
const LABEL_PAD_X = 0.3;
const LABEL_SHADOW = 9;
export const CAPTION_AHEAD = 0.45;

export const captionWord = (word: string): string => str(word);

const wordWidth = (word: string, size: number) => textWidth(word, size) + size * PAD * 2;

export const lineWidth = (words: string[], size: number): number =>
  words.reduce((sum, w, i) => sum + wordWidth(w, size) + (i > 0 ? size * GAP : 0), 0);

export type CaptionLayout = { size: number; lines: string[][] };

const bestSplit = (words: string[], size: number): { lines: string[][]; width: number } | null => {
  const n = words.length;
  let best: { lines: string[][]; width: number } | null = null;
  for (let k = 1; k < n; k++) {
    const a = words.slice(0, k);
    const b = words.slice(k);
    if (n >= 4 && (a.length < 2 || b.length < 2)) continue;
    const width = Math.max(lineWidth(a, size), lineWidth(b, size));
    if (width > CAPTION_ROW) continue;
    const score = width + (n === 3 && b.length === 1 && textWidth(b[0], size) < size * 3 ? size * 4 : 0);
    if (!best || score < best.width) best = { lines: [a, b], width: score };
  }
  return best;
};

export const captionLayout = (raw: string[]): CaptionLayout => {
  const words = raw.map(captionWord).filter((w) => w.length > 0);
  if (words.length === 0) return { size: CAPTION_MAX, lines: [] };
  for (let size = CAPTION_MAX; size >= CAPTION_ONE_LINE_MIN; size -= 2) {
    if (lineWidth(words, size) <= CAPTION_ROW) return { size, lines: [words] };
  }
  if (words.length === 1) {
    let size = CAPTION_ONE_LINE_MIN;
    while (size > 30 && lineWidth(words, size) > CAPTION_ROW) size -= 2;
    return { size, lines: [words] };
  }
  if (words.length === 3) {
    for (let size = CAPTION_ONE_LINE_MIN; size >= CAPTION_MIN; size -= 2) {
      if (lineWidth(words, size) <= CAPTION_ROW) return { size, lines: [words] };
    }
  }
  for (let size = CAPTION_TWO_LINE_MAX; size >= CAPTION_MIN; size -= 2) {
    const split = bestSplit(words, size);
    if (split) return { size, lines: split.lines };
  }
  let size = CAPTION_MIN;
  let split = bestSplit(words, size);
  while (!split && size > 30) {
    size -= 2;
    split = bestSplit(words, size);
  }
  return { size, lines: split ? split.lines : [words] };
};

export const captionSize = (words: string[]): number => captionLayout(words).size;

const LONE_MARK = /^[:;!?»%…]+$/;

export type CaptionToken = { w: string; from: number; to: number; first: number };

export const captionTokens = (words: { w: string; from: number; to: number }[]): CaptionToken[] =>
  words.reduce<CaptionToken[]>((tokens, word, i) => {
    const text = captionWord(word.w);
    if (!text) return tokens;
    const prev = tokens[tokens.length - 1];
    if (prev && LONE_MARK.test(text)) {
      tokens[tokens.length - 1] = { ...prev, w: `${prev.w}\u00a0${text}`, to: word.to };
      return tokens;
    }
    tokens.push({ w: text, from: word.from, to: word.to, first: i });
    return tokens;
  }, []);

export const currentWordIndex = (group: CaptionGroup, frame: number): number => {
  let index = 0;
  group.words.forEach((word, i) => {
    if (frame >= word.from) index = i;
  });
  return index;
};

export const captionTilt = (from: number): number => (Math.floor(from / 7) % 2 === 0 ? -2 : 2);

export const Captions: React.FC<{ groups: CaptionGroup[] }> = ({ groups }) => {
  const frame = useCurrentFrame();
  const group = groups.find((g) => frame >= g.from && frame < g.to);
  if (!group) return null;
  const words = captionTokens(group.words);
  const active = currentWordIndex({ ...group, words }, frame);
  const { size, lines } = captionLayout(words.map((w) => w.w));
  const pop = interpolate(frame - group.from, [0, 4], [0.86, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const edge = cutEdge(`caption-${group.from}`, 0.8);
  let index = 0;

  return (
    <div
      style={{
        position: "absolute",
        left: content.left,
        width: content.width,
        top: layout.captionTop,
        transform: `scale(${layout.safeScale})`,
        transformOrigin: "50% 0",
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div style={{ position: "relative", transform: `rotate(${captionTilt(group.from)}deg) scale(${pop})` }}>
        <div style={{ position: "absolute", inset: 0, transform: `translate(${LABEL_SHADOW * 0.8}px, ${LABEL_SHADOW}px)`, background: shade, clipPath: edge }} />
        <div style={{ position: "absolute", inset: 0, background: colors.ink, clipPath: edge }} />
        <div
          style={{
            position: "relative",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: `${size * LABEL_PAD_Y}px ${size * LABEL_PAD_X}px`,
            fontFamily: fonts.text,
            fontWeight: 800,
            fontSize: size,
            lineHeight: CAPTION_LINE,
          }}
        >
          {lines.map((line, li) => (
            <div key={`line-${li}`} style={{ display: "flex", gap: size * GAP, whiteSpace: "nowrap" }}>
              {line.map((text) => {
                const i = index++;
                return (
                  <span
                    key={`${group.from}-${i}`}
                    style={{
                      padding: `0 ${size * PAD}px`,
                      color: i === active ? colors.yellow : colors.cream,
                      opacity: i > active ? CAPTION_AHEAD : 1,
                    }}
                  >
                    {text}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
