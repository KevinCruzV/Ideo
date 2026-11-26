import React from "react";
import { colors, fonts, layout } from "../theme";
import { fitText } from "../text/fit";
import { Chapter } from "../types";

export const CHAPTER_TOP = layout.marginTop + 6;
export const CHAPTER_LINE_HEIGHT = 1.12;
const CHAPTER_FIT = { maxWidth: 600, maxLines: 2, max: 38, min: 28 };

export const chapterText = (chapter: Chapter): string =>
  chapter.total === 1 ? chapter.title : `${chapter.label} ${chapter.part} · ${chapter.title}`;

export const chapterFit = (chapter: Chapter) => fitText(chapterText(chapter), CHAPTER_FIT);

export const chapterBottom = (chapter: Chapter): number => {
  const fit = chapterFit(chapter);
  return CHAPTER_TOP + fit.lines.length * fit.size * CHAPTER_LINE_HEIGHT;
};

export const ChapterLabel: React.FC<{ chapter: Chapter }> = ({ chapter }) => {
  const fit = chapterFit(chapter);
  return (
    <div
      style={{
        position: "absolute",
        top: CHAPTER_TOP,
        left: layout.marginSide,
        maxWidth: CHAPTER_FIT.maxWidth,
        color: colors.cream,
        background: colors.ink,
        padding: "8px 22px",
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
