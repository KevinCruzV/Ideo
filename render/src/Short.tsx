import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile } from "remotion";
import { Background } from "./chrome/Background";
import { Captions } from "./chrome/Captions";
import { ChapterCard } from "./chrome/ChapterCard";
import { ChapterLabel } from "./chrome/ChapterLabel";
import { Progress } from "./chrome/Progress";
import { Watermark } from "./chrome/Watermark";
import { Wipe, wipeKind, WIPE_BEFORE, WIPE_FRAMES } from "./chrome/Wipe";
import { AccentContext } from "./scenes/accent";
import { BeatsContext, localBeats } from "./scenes/beats";
import { cleanItems, earlyItems, str } from "./scenes/coerce";
import { punchCuts } from "./scenes/punch";
import { resolveScene } from "./scenes/registry";
import { SceneFrame } from "./scenes/SceneFrame";
import { colors, moodOf, segmentAccent, setMood } from "./theme";
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
        const beats = localBeats(segment.beats, segment.from, segment.to);
        const cuts = punchCuts([...(segment.items ?? []).map((it) => Math.round(it.at - segment.from)), ...beats], duration);
        const kicker = str(props.kicker);
        return (
          <Sequence key={`${segment.kind}-${i}`} from={segment.from} durationInFrames={duration} layout="none">
            <Background color={colors[accents[i].accent]} />
            <AccentContext.Provider value={accents[i].accent}>
              <BeatsContext.Provider value={beats}>
              <SceneFrame props={props} duration={duration} last={i === count - 1} index={i} cuts={cuts}>
                <Scene props={props} items={segment.type === "object-state" ? cleanItems(segment.items) : earlyItems(cleanItems(segment.items), segment.from)} from={segment.from} to={segment.to} />
              </SceneFrame>
              </BeatsContext.Provider>
            </AccentContext.Provider>
            {segment.break === true && kicker ? <ChapterCard text={kicker} accent={accents[i].accent} duration={duration} /> : null}
          </Sequence>
        );
      })}
      {timeline.segments.slice(1).map((segment, i) => (
        <Sequence key={`wipe-${i}`} from={segment.from - WIPE_BEFORE} durationInFrames={WIPE_FRAMES + 1} layout="none">
          <Wipe color={accents[i + 1].accent} seed={`wipe-${i}`} kind={wipeKind(i)} />
        </Sequence>
      ))}
      <ChapterLabel chapter={timeline.chapter} />
      <Watermark text={timeline.watermark} />
      <Progress chapter={timeline.chapter} segments={timeline.segments} />
      <Captions groups={timeline.captions} />
    </AbsoluteFill>
  );
};
