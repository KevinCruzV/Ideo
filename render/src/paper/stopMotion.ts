export const STEP_FPS = 12;

export const stepFrame = (frame: number, fps = 30, stepFps = STEP_FPS): number => {
  const size = fps / stepFps;
  return Math.floor(frame / size) * size;
};

const hash = (input: string): number => {
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

export const jitter = (seed: string, frame: number, maxDeg = 2.5): number => {
  const step = Math.round(stepFrame(frame) * 1000);
  return (hash(`${seed}:${step}`) * 2 - 1) * maxDeg;
};
