import { jitter, stepIndex } from "../paper/stopMotion";

export type Pose = "question" | "surprise" | "montre" | "content";

export const POSES: readonly Pose[] = ["question", "surprise", "montre", "content"];

export const poseOf = (value: unknown): Pose => {
  if (typeof value !== "string") return "question";
  const clean = value.trim().toLowerCase();
  return (POSES as readonly string[]).includes(clean) ? (clean as Pose) : "question";
};

export type Mouth = "flat" | "open" | "smile";

export type PoseSpec = {
  headTilt: number;
  lean: number;
  eyeR: number;
  pupilR: number;
  look: [number, number];
  mouth: Mouth;
  arm: boolean;
};

export const POSE_SPECS: Record<Pose, PoseSpec> = {
  question: { headTilt: 8, lean: 0, eyeR: 7.5, pupilR: 3.4, look: [2.3, -2.8], mouth: "flat", arm: false },
  surprise: { headTilt: -3, lean: -7, eyeR: 9, pupilR: 3, look: [0.4, -0.6], mouth: "open", arm: false },
  montre: { headTilt: 4, lean: 3, eyeR: 7.5, pupilR: 3.4, look: [3.4, 0.4], mouth: "smile", arm: true },
  content: { headTilt: -6, lean: 0, eyeR: 7.5, pupilR: 3.4, look: [2, 1], mouth: "smile", arm: false },
};

const HOLD_STEPS = 5;

export const idleTilt = (seed: string, frame: number): number => {
  const beat = Math.floor(stepIndex(frame) / HOLD_STEPS);
  return Math.round(jitter(`${seed}:tilt`, beat * 30, 2));
};

const unit = (seed: string, k: number): number => (jitter(`${seed}:blink:${k}`, 0, 1) + 1) / 2;

export const BLINK_FRAMES = 4;

export const blinkStarts = (seed: string, until: number, fps = 30): number[] => {
  const starts: number[] = [];
  let t = Math.round(fps * (0.9 + unit(seed, -1) * 0.6));
  let k = 0;
  while (t <= until) {
    starts.push(t);
    t += Math.round(fps * (3 + unit(seed, k)));
    k += 1;
  }
  return starts;
};

export const isBlinking = (seed: string, frame: number, fps = 30): boolean => {
  if (frame < 0) return false;
  const starts = blinkStarts(seed, frame, fps);
  const last = starts[starts.length - 1];
  return last !== undefined && frame - last < BLINK_FRAMES;
};

const HOP = [0.07, 0.035];

export const LAND_FRAMES = 5;

export const hopLift = (frame: number, landAt: number): number => {
  const local = frame - landAt;
  if (local < 0) return 0;
  const step = stepIndex(local);
  return step < HOP.length ? HOP[step] : 0;
};
