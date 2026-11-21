import { hash } from "../paper/motion";

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
  surprise: { headTilt: -3, lean: -4, eyeR: 9, pupilR: 3, look: [0.4, -0.6], mouth: "open", arm: false },
  montre: { headTilt: 4, lean: 2, eyeR: 7.5, pupilR: 3.4, look: [3.4, 0.4], mouth: "smile", arm: true },
  content: { headTilt: -6, lean: 0, eyeR: 7.5, pupilR: 3.4, look: [2, 1], mouth: "smile", arm: false },
};

export const idleTilt = (seed: string, frame: number): number => {
  const phase = hash(`${seed}:tilt`) * Math.PI * 2;
  return 2 * Math.sin((frame / 30) * 1.1 + phase) * Math.cos((frame / 30) * 0.37);
};

export const breath = (frame: number): number => 1 + 0.012 * Math.sin((frame / 30) * Math.PI * 2 * 0.28);

export const gaze = (seed: string, frame: number): [number, number] => {
  const a = hash(`${seed}:gx`) * Math.PI * 2;
  const b = hash(`${seed}:gy`) * Math.PI * 2;
  const t = frame / 30;
  return [1.4 * Math.sin(t * 0.7 + a) + 0.6 * Math.sin(t * 1.9 + b), 0.9 * Math.sin(t * 0.5 + b)];
};

const unit = (seed: string, k: number): number => hash(`${seed}:blink:${k}`);

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

export const HOP_FRAMES = 14;

export const LAND_FRAMES = 4;

export const hopLift = (frame: number, landAt: number): number => {
  const local = frame - landAt;
  if (local < 0 || local >= HOP_FRAMES) return 0;
  const t = local / HOP_FRAMES;
  return 0.05 * Math.sin(t * Math.PI) * (1 - t * 0.5);
};
