import { interpolate, spring } from "remotion";

export const FPS = 30;

export const hash = (input: string): number => {
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  h ^= h >>> 15;
  h = Math.imul(h, 2246822507);
  h ^= h >>> 13;
  h = Math.imul(h, 3266489909);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967295;
};

export const signed = (seed: string, max = 1): number => (hash(seed) * 2 - 1) * max;

export const restTilt = (seed: string, max = 1.6): number => signed(`${seed}:tilt`, max);

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const ENTER_CONFIG = { damping: 13, stiffness: 150, mass: 0.8 } as const;

export const enterProgress = (frame: number, at: number, fps = FPS): number =>
  frame < at ? 0 : spring({ frame: frame - at, fps, config: ENTER_CONFIG });

export type Entry = { opacity: number; x: number; y: number; rotate: number; scale: number; progress: number };

export type EntryOptions = { dx?: number; dy?: number; spin?: number; from?: number; fps?: number };

export const MIN_SCALE = 0.92;

export const SUPPORT_AT = -3;

export const entry = (frame: number, at: number, { dx = 0, dy = 36, spin = 3, from = MIN_SCALE, fps = FPS }: EntryOptions = {}): Entry => {
  const local = frame - at;
  if (local < 0) return { opacity: 0, x: dx, y: dy, rotate: spin, scale: from, progress: 0 };
  const p = enterProgress(frame, at, fps);
  const rest = 1 - p;
  return {
    opacity: interpolate(local, [0, 3], [0, 1], clamp),
    x: dx * rest,
    y: dy * rest,
    rotate: spin * rest,
    scale: Math.max(from, from + (1 - from) * p),
    progress: p,
  };
};

export type Drift = { x: number; y: number; r: number };

export const drift = (seed: string, frame: number, amp = 3, spin = 0.35, fps = FPS): Drift => {
  const a = hash(`${seed}:a`);
  const b = hash(`${seed}:b`);
  const c = hash(`${seed}:c`);
  const px = (3.4 + a * 2.2) * fps;
  const py = (4.1 + b * 2.4) * fps;
  const pr = (5 + c * 2.5) * fps;
  const t = 2 * Math.PI;
  return {
    x: amp * Math.sin((t * frame) / px + a * t),
    y: amp * 0.8 * Math.sin((t * frame) / py + b * t),
    r: spin * Math.sin((t * frame) / pr + c * t),
  };
};

export const paperTransform = (e: Entry, d: Drift, tilt: number): string =>
  `translate(${(e.x + d.x).toFixed(2)}px, ${(e.y + d.y).toFixed(2)}px) rotate(${(tilt + e.rotate + d.r).toFixed(3)}deg) scale(${e.scale.toFixed(4)})`;

export const tween = (frame: number, at: number, length = 14): number =>
  interpolate(frame - at, [0, length], [0, 1], { ...clamp, easing: (t) => 1 - Math.pow(1 - t, 3) });

const pct = (v: number) => `${v.toFixed(2)}%`;

export const cutEdge = (seed: string, amount = 1.2): string => {
  const j = (k: string, max = amount) => signed(`${seed}:${k}`, max);
  const pts: [number, number][] = [
    [0 + Math.abs(j("a")), 0 + Math.abs(j("b", amount * 3))],
    [33 + j("c", 6), 0 + Math.abs(j("d", amount * 2))],
    [67 + j("e", 6), 0 + Math.abs(j("f", amount * 2.5))],
    [100 - Math.abs(j("g")), 0 + Math.abs(j("h", amount * 3))],
    [100 - Math.abs(j("i", amount * 0.8)), 50 + j("i2", 10)],
    [100 - Math.abs(j("k")), 100 - Math.abs(j("l", amount * 3))],
    [60 + j("m", 6), 100 - Math.abs(j("n", amount * 2))],
    [30 + j("o", 6), 100 - Math.abs(j("p", amount * 2.5))],
    [0 + Math.abs(j("q")), 100 - Math.abs(j("r", amount * 3))],
    [0 + Math.abs(j("s", amount * 0.8)), 50 + j("s2", 10)],
  ];
  return `polygon(${pts.map(([x, y]) => `${pct(x)} ${pct(y)}`).join(", ")})`;
};

export const cutCircle = (seed: string, points = 30, rough = 0.9): string => {
  const pts = Array.from({ length: points }, (_, i) => {
    const angle = (i / points) * Math.PI * 2;
    const r = 50 - Math.abs(signed(`${seed}:${i}`, rough));
    return `${pct(50 + r * Math.cos(angle))} ${pct(50 + r * Math.sin(angle))}`;
  });
  return `polygon(${pts.join(", ")})`;
};

export const cutPolygon = (seed: string, points: [number, number][], rough = 1): string =>
  `polygon(${points
    .map(([x, y], i) => `${pct(x + signed(`${seed}:x${i}`, rough))} ${pct(y + signed(`${seed}:y${i}`, rough))}`)
    .join(", ")})`;
