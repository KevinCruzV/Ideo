import React from "react";
import { useCurrentFrame } from "remotion";

export const BEAT_FRAMES = 12;

export const BeatsContext = React.createContext<number[]>([]);

export type Beat = { index: number; t: number; wave: number };

export const localBeats = (value: unknown, from: number, to: number): number[] =>
  Array.isArray(value)
    ? value
        .filter((v): v is number => typeof v === "number" && Number.isFinite(v))
        .map((v) => Math.round(v - from))
        .filter((v) => v >= 0 && v < to - from)
        .sort((a, b) => a - b)
    : [];

export const beatAt = (beats: number[], frame: number, length = BEAT_FRAMES): Beat | null => {
  for (let i = beats.length - 1; i >= 0; i--) {
    const local = frame - beats[i];
    if (local < 0) continue;
    if (local >= length) return null;
    const t = local / length;
    return { index: i, t, wave: Math.sin(t * Math.PI) };
  }
  return null;
};

export const beatsBefore = (beats: number[], frame: number): number => beats.filter((b) => b <= frame).length;

export const useBeat = (length = BEAT_FRAMES): Beat | null => {
  const beats = React.useContext(BeatsContext);
  const frame = useCurrentFrame();
  return beatAt(beats, frame, length);
};

export const useBeats = (): number[] => React.useContext(BeatsContext);
