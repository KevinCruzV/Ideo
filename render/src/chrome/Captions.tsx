import React from "react";
import { useCurrentFrame } from "remotion";
import { accentAt, AccentSpan, colors, fonts, layout, onPaper, shadowFilter, stripClip } from "../theme";
import { jitter } from "../paper/stopMotion";
import { textWidth } from "../text/fit";
import { str } from "../scenes/coerce";
import { CaptionGroup } from "../types";

const FONT_SIZE = 76;
const MIN_SIZE = 52;
const MAX_LINES = 2;
const ROW_WIDTH = layout.width - layout.marginSide * 2;

export const captionWord = (word: string): string => str(word);

export const captionSize = (words: string[]): number => {
  for (let size = FONT_SIZE; size > MIN_SIZE; size -= 2) {
    const gap = 14;
    const pad = size * 0.4;
    let lines = 1;
    let width = 0;
    for (const w of words) {
      const wordW = textWidth(w, size) + pad;
      if (width > 0 && width + gap + wordW > ROW_WIDTH) {
        lines += 1;
        width = wordW;
      } else width += (width > 0 ? gap : 0) + wordW;
      if (wordW > ROW_WIDTH) lines += 1;
    }
    if (lines <= MAX_LINES) return size;
  }
  return MIN_SIZE;
};

export const currentWordIndex = (group: CaptionGroup, frame: number): number => {
  let index = 0;
  group.words.forEach((word, i) => {
    if (frame >= word.from) index = i;
  });
  return index;
};

export const Captions: React.FC<{ groups: CaptionGroup[]; accents?: AccentSpan[] }> = ({
  groups,
  accents = [],
}) => {
  const frame = useCurrentFrame();
  const group = groups.find((g) => frame >= g.from && frame < g.to);
  if (!group) return null;
  const active = currentWordIndex(group, frame);
  const accent = accentAt(accents, frame);
  const size = captionSize(group.words.map((w) => w.w));

  return (
    <div
      style={{
        position: "absolute",
        left: layout.marginSide,
        right: layout.marginSide,
        bottom: layout.captionBottom,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: "10px 14px",
        fontFamily: fonts.text,
        fontWeight: 800,
        fontSize: size,
        lineHeight: 1.15,
      }}
    >
      {group.words.map((word, i) => {
        const isActive = i === active;
        const upcoming = i > active;
        return (
          <span
            key={`${group.from}-${i}`}
            style={{
              display: "inline-block",
              opacity: upcoming ? 0.4 : 1,
              transform: isActive ? `rotate(${jitter(`${group.from}-${i}`, frame, 2)}deg)` : undefined,
              filter: isActive ? shadowFilter : undefined,
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: `0 ${size * 0.2}px`,
                background: isActive ? colors[accent] : "transparent",
                color: isActive ? onPaper[accent] : colors.ink,
                clipPath: isActive ? stripClip : undefined,
              }}
            >
              {captionWord(word.w)}
            </span>
          </span>
        );
      })}
    </div>
  );
};
