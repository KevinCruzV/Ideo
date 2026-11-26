import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { colors, content, layout } from "../theme";
import { Chapter } from "../types";

export type Tick = { from: number; to: number };

export const progressTicks = (
  chapter: Chapter,
  segments: Tick[],
  frame: number,
  durationInFrames: number,
): { weight: number; fill: number }[] => {
  const clamp = (v: number) => Math.min(1, Math.max(0, v));
  if (chapter.total === 1 && segments.length > 0) {
    return segments.map((s) => {
      const length = Math.max(1, s.to - s.from);
      return { weight: length, fill: clamp((frame - s.from + 1) / length) };
    });
  }
  return [{ weight: 1, fill: clamp(frame / Math.max(1, durationInFrames - 1)) }];
};

export const Progress: React.FC<{ chapter: Chapter; segments?: Tick[] }> = ({ chapter, segments = [] }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const ticks = progressTicks(chapter, segments, frame, durationInFrames);
  const gap = Math.min(12, Math.max(3, Math.floor(240 / ticks.length)));

  return (
    <div
      style={{
        position: "absolute",
        left: layout.safeCenterX - (content.width * layout.chromeScale) / 2,
        right: layout.width - layout.safeCenterX - (content.width * layout.chromeScale) / 2,
        top: layout.progressTop,
        height: layout.progressHeight,
        display: "flex",
        gap,
      }}
    >
      {ticks.map((tick, i) => (
        <div
          key={i}
          style={{
            flex: tick.weight,
            height: "100%",
            background: colors.track,
            overflow: "hidden",
          }}
        >
          <div style={{ width: `${tick.fill * 100}%`, height: "100%", background: colors.fg }} />
        </div>
      ))}
    </div>
  );
};
