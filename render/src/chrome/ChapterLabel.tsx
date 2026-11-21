import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, fonts, layout } from "../theme";
import { jitter } from "../paper/stopMotion";
import { Chapter } from "../types";

export const chapterText = (chapter: Chapter): string =>
  chapter.total === 1 ? chapter.title : `${chapter.label} ${chapter.part} · ${chapter.title}`;

export const ChapterLabel: React.FC<{ chapter: Chapter }> = ({ chapter }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: "absolute",
        top: layout.marginTop + 8,
        left: layout.marginSide,
        maxWidth: 600,
        color: colors.ink,
        fontFamily: fonts.text,
        fontWeight: 800,
        fontSize: 40,
        lineHeight: 1.1,
        transform: `rotate(${-2 + jitter("chapter", frame, 0.6)}deg)`,
        transformOrigin: "left top",
      }}
    >
      {chapterText(chapter)}
    </div>
  );
};
