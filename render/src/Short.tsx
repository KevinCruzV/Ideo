import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Background } from "./chrome/Background";
import { Captions } from "./chrome/Captions";
import { ChapterLabel } from "./chrome/ChapterLabel";
import { Progress } from "./chrome/Progress";
import { Watermark } from "./chrome/Watermark";
import { Wipe, WIPE_BEFORE, WIPE_FRAMES } from "./chrome/Wipe";
import { AccentContext } from "./scenes/accent";
import { BeatsContext, localBeats } from "./scenes/beats";
import { cleanItems, earlyItems } from "./scenes/coerce";
import { resolveScene } from "./scenes/registry";
import { SceneFrame } from "./scenes/SceneFrame";
import { moodOf, segmentAccent, setMood } from "./theme";
import { Timeline } from "./types";

export const Short: React.FC<Timeline> = (timeline) => {
  setMood(moodOf(timeline.mood));
  const accents = timeline.segments.map((segment, i) => ({
    from: segment.from,
    to: segment.to,
    accent: segmentAccent(i, segment.kind === "scene" ? segment.type : undefined),
  }));
  const count = timeline.segments.length;
  return (
    <AbsoluteFill>
      <Background />
      {timeline.audio ? <Audio src={staticFile(timeline.audio)} /> : null}
      {timeline.segments.map((segment, i) => {
        const Scene = resolveScene(segment);
        const props = segment.props && typeof segment.props === "object" ? segment.props : {};
        const duration = Math.max(1, segment.to - segment.from);
        return (
          <Sequence key={`${segment.kind}-${i}`} from={segment.from} durationInFrames={duration} layout="none">
            <AccentContext.Provider value={accents[i].accent}>
              <BeatsContext.Provider value={localBeats(segment.beats, segment.from, segment.to)}>
              <SceneFrame props={props} duration={duration} last={i === count - 1}>
                <Scene props={props} items={segment.type === "object-state" ? cleanItems(segment.items) : earlyItems(cleanItems(segment.items), segment.from)} from={segment.from} to={segment.to} />
              </SceneFrame>
              </BeatsContext.Provider>
            </AccentContext.Provider>
          </Sequence>
        );
      })}
      {timeline.segments.slice(1).map((segment, i) => (
        <Sequence key={`wipe-${i}`} from={segment.from - WIPE_BEFORE} durationInFrames={WIPE_FRAMES + 1} layout="none">
          <Wipe color={accents[i + 1].accent} seed={`wipe-${i}`} />
        </Sequence>
      ))}
      <ChapterLabel chapter={timeline.chapter} />
      <Watermark text={timeline.watermark} />
      <Progress chapter={timeline.chapter} segments={timeline.segments} />
      <Captions groups={timeline.captions} accents={accents} />
    </AbsoluteFill>
  );
};
