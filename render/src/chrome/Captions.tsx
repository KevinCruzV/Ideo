import React from "react";
import { useCurrentFrame } from "remotion";
import { accentAt, AccentSpan, colors, fonts, layout, onPaper, shadowFilter, stripClip } from "../theme";
import { jitter } from "../paper/stopMotion";
import { CaptionGroup } from "../types";

const FONT_SIZE = 76;

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
        fontSize: FONT_SIZE,
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
                padding: `0 ${FONT_SIZE * 0.2}px`,
                background: isActive ? colors[accent] : "transparent",
                color: isActive ? onPaper[accent] : colors.ink,
                clipPath: isActive ? stripClip : undefined,
              }}
            >
              {word.w}
            </span>
          </span>
        );
      })}
    </div>
  );
};
