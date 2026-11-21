import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Captions } from "./chrome/Captions";
import { ChapterLabel } from "./chrome/ChapterLabel";
import { Progress } from "./chrome/Progress";
import { Watermark } from "./chrome/Watermark";
import { AccentContext } from "./scenes/accent";
import { cleanItems } from "./scenes/coerce";
import { resolveScene } from "./scenes/registry";
import { colors, segmentAccent } from "./theme";
import { Timeline } from "./types";

export const Short: React.FC<Timeline> = (timeline) => {
  const accents = timeline.segments.map((segment, i) => ({
    from: segment.from,
    to: segment.to,
    accent: segmentAccent(i, segment.kind === "scene" ? segment.type : undefined),
  }));
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
            <AccentContext.Provider value={accents[i].accent}>
              <AbsoluteFill>
                <Scene
                  props={segment.props && typeof segment.props === "object" ? segment.props : {}}
                  items={cleanItems(segment.items)}
                  from={segment.from}
                  to={segment.to}
                />
              </AbsoluteFill>
            </AccentContext.Provider>
          </Sequence>
        );
      })}
      <ChapterLabel chapter={timeline.chapter} />
      <Watermark text={timeline.watermark} />
      <Progress chapter={timeline.chapter} segments={timeline.segments} />
      <Captions groups={timeline.captions} accents={accents} />
    </AbsoluteFill>
  );
};
