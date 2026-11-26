import React from "react";
import { colors, fonts, layout } from "../theme";
import { fitText, textWidth } from "../text/fit";
import { Chapter } from "../types";
import { watermarkLeft } from "./Watermark";

export const CHAPTER_TOP = layout.marginTop + 6;
export const CHAPTER_LINE_HEIGHT = 1.12;
export const CHAPTER_PAD = 22;
export const CHAPTER_GAP = 44;
export const DEFAULT_WATERMARK = "@idevideos";
const CHAPTER_FIT = { maxLines: 3, max: 38, min: 24 };

const chapterRoom = (watermark: string): number =>
  Math.min(520, (watermarkLeft(watermark) - CHAPTER_GAP - layout.marginSide - CHAPTER_PAD * 2) * 0.96);

export const chapterText = (chapter: Chapter): string =>
  chapter.total === 1 ? chapter.title : `${chapter.label} ${chapter.part} · ${chapter.title}`;

export const chapterFit = (chapter: Chapter, watermark: string = DEFAULT_WATERMARK) => {
  const options = { ...CHAPTER_FIT, maxWidth: chapterRoom(watermark) };
  const text = chapterText(chapter);
  const two = fitText(text, { ...options, maxLines: 2 });
  return two.lines.some((l) => l.includes("…") || l.endsWith("-")) ? fitText(text, options) : two;
};

export const chapterBoxRight = (chapter: Chapter, watermark: string = DEFAULT_WATERMARK): number => {
  const fit = chapterFit(chapter, watermark);
  return layout.marginSide + Math.max(0, ...fit.lines.map((l) => textWidth(l, fit.size))) + CHAPTER_PAD * 2;
};

export const chapterBottom = (chapter: Chapter, watermark: string = DEFAULT_WATERMARK): number => {
  const fit = chapterFit(chapter, watermark);
  return CHAPTER_TOP + fit.lines.length * fit.size * CHAPTER_LINE_HEIGHT;
};

export const ChapterLabel: React.FC<{ chapter: Chapter; watermark?: string }> = ({ chapter, watermark = DEFAULT_WATERMARK }) => {
  const fit = chapterFit(chapter, watermark);
  return (
    <div
      style={{
        position: "absolute",
        top: CHAPTER_TOP,
        left: layout.marginSide,
        color: colors.cream,
        background: colors.ink,
        padding: `8px ${CHAPTER_PAD}px`,
        borderRadius: 999,
        fontFamily: fonts.text,
        fontWeight: 800,
        fontSize: fit.size,
        lineHeight: CHAPTER_LINE_HEIGHT,
        whiteSpace: "nowrap",
      }}
    >
      {fit.lines.map((line, i) => (
        <div key={`chapter-${i}`}>{line}</div>
      ))}
    </div>
  );
};
