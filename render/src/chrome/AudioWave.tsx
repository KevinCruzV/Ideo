import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { tornEdge } from "../paper/Sheet";
import { PictoArt } from "../pictos/Picto";
import { AccentColor, colors, layout, shade } from "../theme";

export const WAVE_BARS = 24;
export const WAVE_FLOOR = 0.08;
const WAVE_W = 560;
const WAVE_H = 130;
const BAR_W = 12;
const POP = 5;

const clamp = (v: number) => Math.min(1, Math.max(WAVE_FLOOR, Number.isFinite(v) ? v : 0));

export const waveBars = (levels: number[], frame: number): number[] =>
  Array.from({ length: WAVE_BARS }, (_, i) => {
    const at = frame - (WAVE_BARS - 1 - i);
    return at < 0 || at >= levels.length ? WAVE_FLOOR : clamp(levels[at]);
  });

export type SegmentAudio = { kind: string; start: number; levels: number[] };

export const SegmentAudioContext = React.createContext<SegmentAudio | null>(null);

export const useSegmentAudio = (): SegmentAudio | null => React.useContext(SegmentAudioContext);

export const AudioWave: React.FC<{ levels: number[]; start?: number; accent: AccentColor; width?: number; height?: number }> = ({
  levels,
  start = 0,
  accent,
  width = WAVE_W,
  height = WAVE_H,
}) => {
  const frame = useCurrentFrame() - start;
  const length = levels.length;
  if (frame < 0 || frame >= length) return null;
  const show = interpolate(frame, [0, POP, Math.max(POP + 1, length - POP), Math.max(POP + 2, length)], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const bars = waveBars(levels, frame);
  const edge = tornEdge("audio-wave", 10, 3);
  const bar = accent === "yellow" ? colors.cream : colors.yellow;
  const mic = Math.round(height * 0.74);
  const barMax = Math.round(height * 0.7);
  return (
    <div style={{ position: "relative", width, height, opacity: show, transform: `rotate(-2deg) scale(${0.85 + 0.15 * show})` }}>
      <div style={{ position: "absolute", inset: 0, transform: "translate(6px, 8px)", background: shade, clipPath: edge }} />
      <div style={{ position: "absolute", inset: 0, background: colors.ink, clipPath: edge }} />
      <div style={{ position: "absolute", left: 14, top: (height - mic) / 2 }}>
        <PictoArt name="microphone" size={mic} />
      </div>
      <div style={{ position: "absolute", left: mic + 26, right: 18, top: 0, bottom: 0, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {bars.map((level, i) => (
          <div key={`bar-${i}`} style={{ width: BAR_W, height: Math.max(4, Math.round(barMax * level)), borderRadius: BAR_W / 2, background: bar }} />
        ))}
      </div>
    </div>
  );
};

export const SfxWave: React.FC<{ levels: number[]; accent: AccentColor }> = ({ levels, accent }) => (
  <div style={{ position: "absolute", left: layout.safeCenterX - WAVE_W / 2, top: (layout.captionTop + layout.captionBottom - WAVE_H) / 2 }}>
    <AudioWave levels={levels} accent={accent} />
  </div>
);
