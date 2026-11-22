export const BODY_POSES = [
  "standing",
  "sitting",
  "walking",
  "running",
  "lying-back",
  "lying-starfish",
  "lying-side-left",
  "lying-side-right",
  "lying-fetal",
  "lying-stomach",
] as const;

export const BODY_SETTINGS = ["none", "bed", "chair", "desk", "outdoor"] as const;

export const BODY_PARTS = [
  "head",
  "brain",
  "neck",
  "throat",
  "shoulders",
  "chest",
  "heart",
  "lungs",
  "stomach",
  "back",
  "spine",
  "hips",
  "arms",
  "hands",
  "knees",
  "legs",
  "feet",
] as const;

export const BODY_TONES = ["good", "bad", "neutral"] as const;

export type BodyPose = (typeof BODY_POSES)[number];
export type BodySetting = (typeof BODY_SETTINGS)[number];
export type BodyPart = (typeof BODY_PARTS)[number];
export type BodyTone = (typeof BODY_TONES)[number];

const pick = <T extends string>(options: readonly T[], value: unknown, fallback: T): T => {
  if (typeof value !== "string") return fallback;
  const clean = value.trim().toLowerCase();
  return (options as readonly string[]).includes(clean) ? (clean as T) : fallback;
};

export const bodyPose = (value: unknown): BodyPose => pick(BODY_POSES, value, "standing");
export const bodySetting = (value: unknown): BodySetting => pick(BODY_SETTINGS, value, "none");
export const bodyTone = (value: unknown): BodyTone => pick(BODY_TONES, value, "neutral");
export const bodyPart = (value: unknown): BodyPart | null => {
  const part = pick(BODY_PARTS as readonly string[], value, "");
  return part ? (part as BodyPart) : null;
};
