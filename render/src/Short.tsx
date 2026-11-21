import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Captions } from "./chrome/Captions";
import { ChapterLabel } from "./chrome/ChapterLabel";
import { Progress } from "./chrome/Progress";
import { Watermark } from "./chrome/Watermark";
import { resolveScene } from "./scenes/registry";
import { colors } from "./theme";
import { Timeline } from "./types";

export const Short: React.FC<Timeline> = (timeline) => {
  return (
    <AbsoluteFill style={{ background: colors.background }}>
      {timeline.audio ? <Audio src={staticFile(timeline.audio)} /> : null}
      {timeline.segments.map((segment, i) => {
        const Scene = resolveScene(segment);
        return (
          <Sequence
            key={`${segment.kind}-${i}`}
            from={segment.from}
            durationInFrames={Math.max(1, segment.to - segment.from)}
            layout="none"
          >
            <AbsoluteFill>
              <Scene segment={segment} />
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <ChapterLabel chapter={timeline.chapter} />
      <Watermark text={timeline.watermark} />
      <Progress chapter={timeline.chapter} />
      <Captions groups={timeline.captions} />
    </AbsoluteFill>
  );
};
