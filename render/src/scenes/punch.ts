import { visibleStageTop } from "../theme";

export const PUNCH_FRAMES = 5;
export const PUNCH_MIN_GAP = 24;
export const PUNCH_LEAD = 18;
export const PUNCH_TAIL = 10;

export type Framing = { s: number; x: number; y: number; r: number };

export const FRAMINGS: readonly Framing[] = [
  { s: 0, x: 0, y: 0, r: 0 },
  { s: 0.04, x: -8, y: 3, r: -0.6 },
  { s: 0.02, x: 8, y: 6, r: 0.5 },
  { s: 0.05, x: 4, y: 4, r: -0.4 },
];

export const PUNCH_ORIGIN_Y = visibleStageTop;

export const punchedY = (y: number, f: Framing): number => PUNCH_ORIGIN_Y + (y - PUNCH_ORIGIN_Y) * (1 + f.s) + f.y;

export const punchCuts = (frames: number[], duration: number): number[] => {
  const cuts: number[] = [];
  for (const f of [...frames].sort((a, b) => a - b)) {
    if (f < PUNCH_LEAD || f > duration - PUNCH_TAIL) continue;
    if (cuts.length > 0 && f - cuts[cuts.length - 1] < PUNCH_MIN_GAP) continue;
    cuts.push(f);
  }
  return cuts;
};

const easeOut = (t: number) => 1 - Math.pow(1 - Math.min(1, Math.max(0, t)), 3);

export const framingAt = (cuts: number[], frame: number): Framing => {
  const k = cuts.filter((c) => c <= frame).length;
  if (k === 0) return FRAMINGS[0];
  const to = FRAMINGS[k % FRAMINGS.length];
  const from = FRAMINGS[(k - 1) % FRAMINGS.length];
  const t = easeOut((frame - cuts[k - 1]) / PUNCH_FRAMES);
  return { s: from.s + (to.s - from.s) * t, x: from.x + (to.x - from.x) * t, y: from.y + (to.y - from.y) * t, r: from.r + (to.r - from.r) * t };
};
