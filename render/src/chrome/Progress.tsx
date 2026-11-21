import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { colors, layout } from "../theme";
import { Chapter } from "../types";

export const Progress: React.FC<{ chapter: Chapter }> = ({ chapter }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const ratio = Math.min(1, Math.max(0, frame / Math.max(1, durationInFrames - 1)));
  const gap = 12;

  return (
    <div
      style={{
        position: "absolute",
        left: layout.marginSide,
        right: layout.marginSide,
        bottom: layout.progressBottom,
        height: layout.progressHeight,
        display: "flex",
        gap,
      }}
    >
      {Array.from({ length: chapter.total }, (_, i) => {
        const part = i + 1;
        const fill = part < chapter.part ? 1 : part === chapter.part ? ratio : 0;
        return (
          <div
            key={part}
            style={{
              flex: 1,
              height: "100%",
              background: "rgba(31,26,20,.16)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${fill * 100}%`,
                height: "100%",
                background: colors.ink,
              }}
            />
          </div>
        );
      })}
    </div>
  );
};
