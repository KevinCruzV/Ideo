export const HAIRS = ["none", "short", "side", "long", "curly", "wild", "bun", "crown-bald"] as const;
export const HAIR_COLORS = ["black", "brown", "blond", "red", "grey", "white"] as const;
export const FACIALS = ["none", "moustache", "beard", "goatee", "sideburns"] as const;
export const HATS = ["none", "cap", "kepi", "bicorne", "crown", "helmet", "top-hat", "beret", "turban", "laurel", "wig"] as const;
export const OUTFITS = ["suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress"] as const;
export const SKINS = ["light", "tan", "brown", "dark"] as const;
export const GENDERS = ["woman", "man"] as const;
export const AGES = ["child", "adult", "old"] as const;
export const JOBS = ["police", "firefighter", "doctor", "judge", "soldier", "worker", "journalist", "lawyer"] as const;
export const JOB_HATS = ["police-cap", "fire-helmet", "hard-hat", "army-helmet"] as const;

export type Hair = (typeof HAIRS)[number];
export type HairColor = (typeof HAIR_COLORS)[number];
export type Facial = (typeof FACIALS)[number];
export type Hat = (typeof HATS)[number];
export type Outfit = (typeof OUTFITS)[number];
export type Skin = (typeof SKINS)[number];
export type Gender = (typeof GENDERS)[number];
export type Age = (typeof AGES)[number];
export type Job = (typeof JOBS)[number];
export type JobHat = (typeof JOB_HATS)[number];

export const JOB_LOOK: Record<Job, { outfit: Job; hat: JobHat | "none" }> = {
  police: { outfit: "police", hat: "police-cap" },
  firefighter: { outfit: "firefighter", hat: "fire-helmet" },
  doctor: { outfit: "doctor", hat: "none" },
  judge: { outfit: "judge", hat: "none" },
  soldier: { outfit: "soldier", hat: "army-helmet" },
  worker: { outfit: "worker", hat: "hard-hat" },
  journalist: { outfit: "journalist", hat: "none" },
  lawyer: { outfit: "lawyer", hat: "none" },
};

export type PersonLook = {
  hair: Hair;
  hairColor: HairColor;
  facial: Facial;
  hat: Hat | JobHat;
  glasses: boolean;
  outfit: Outfit | Job;
  skin: Skin | "paper";
  gender: Gender | "none";
  age: Age | "adult";
};

export const NEUTRAL_LOOK: PersonLook = {
  hair: "short",
  hairColor: "black",
  facial: "none",
  hat: "none",
  glasses: false,
  outfit: "suit",
  skin: "paper",
  gender: "none",
  age: "adult",
};

const pick = <T extends string>(options: readonly T[], value: unknown, fallback: T): T => {
  if (typeof value !== "string") return fallback;
  const clean = value.trim().toLowerCase();
  return (options as readonly string[]).includes(clean) ? (clean as T) : fallback;
};

export const lookOf = (props: Record<string, unknown>): PersonLook => {
  const gender = pick<Gender | "none">([...GENDERS, "none"], props.gender, "none");
  const age = pick<Age>(AGES, props.age, "adult");
  const job = pick<Job | "none">([...JOBS, "none"], props.job, "none");
  const jobLook = job === "none" ? null : JOB_LOOK[job];
  return {
    hair: pick(HAIRS, props.hair, gender === "woman" ? "long" : NEUTRAL_LOOK.hair),
    hairColor: pick(HAIR_COLORS, props.hair_color, age === "old" ? "grey" : NEUTRAL_LOOK.hairColor),
    facial: gender === "woman" || age === "child" ? "none" : pick(FACIALS, props.facial, NEUTRAL_LOOK.facial),
    hat: pick<Hat | JobHat>(HATS, props.hat, jobLook ? jobLook.hat : "none"),
    glasses: props.glasses === true || props.glasses === "true",
    outfit: pick<Outfit | Job>(OUTFITS, props.outfit, jobLook ? jobLook.outfit : gender === "woman" ? "dress" : NEUTRAL_LOOK.outfit),
    skin: typeof props.skin === "string" ? pick(SKINS, props.skin, "light") : "paper",
    gender,
    age,
  };
};

export const HIDES_HAIR_TOP: readonly (Hat | JobHat)[] = ["cap", "kepi", "bicorne", "helmet", "top-hat", "beret", "turban", "wig", "police-cap", "fire-helmet", "hard-hat", "army-helmet"];

export const SKIN_TONES: Record<PersonLook["skin"], string> = {
  paper: "#fbf6ea",
  light: "#f1cfae",
  tan: "#d6a173",
  brown: "#a46a45",
  dark: "#6a412b",
};

export const HAIR_TONES: Record<HairColor, string> = {
  black: "#1f1a14",
  brown: "#6b4226",
  blond: "#e6be5a",
  red: "#c2552c",
  grey: "#8f8a82",
  white: "#f2eee6",
};
