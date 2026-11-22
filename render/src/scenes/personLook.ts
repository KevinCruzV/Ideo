export const HAIRS = ["none", "short", "side", "long", "curly", "wild", "bun", "crown-bald"] as const;
export const HAIR_COLORS = ["black", "brown", "blond", "red", "grey", "white"] as const;
export const FACIALS = ["none", "moustache", "beard", "goatee", "sideburns"] as const;
export const HATS = ["none", "cap", "kepi", "bicorne", "crown", "helmet", "top-hat", "beret", "turban", "laurel", "wig"] as const;
export const OUTFITS = ["suit", "uniform", "robe", "lab-coat", "casual", "toga", "armor", "dress"] as const;
export const SKINS = ["light", "tan", "brown", "dark"] as const;

export type Hair = (typeof HAIRS)[number];
export type HairColor = (typeof HAIR_COLORS)[number];
export type Facial = (typeof FACIALS)[number];
export type Hat = (typeof HATS)[number];
export type Outfit = (typeof OUTFITS)[number];
export type Skin = (typeof SKINS)[number];

export type PersonLook = {
  hair: Hair;
  hairColor: HairColor;
  facial: Facial;
  hat: Hat;
  glasses: boolean;
  outfit: Outfit;
  skin: Skin | "paper";
};

export const NEUTRAL_LOOK: PersonLook = {
  hair: "short",
  hairColor: "black",
  facial: "none",
  hat: "none",
  glasses: false,
  outfit: "suit",
  skin: "paper",
};

const pick = <T extends string>(options: readonly T[], value: unknown, fallback: T): T => {
  if (typeof value !== "string") return fallback;
  const clean = value.trim().toLowerCase();
  return (options as readonly string[]).includes(clean) ? (clean as T) : fallback;
};

export const lookOf = (props: Record<string, unknown>): PersonLook => ({
  hair: pick(HAIRS, props.hair, NEUTRAL_LOOK.hair),
  hairColor: pick(HAIR_COLORS, props.hair_color, NEUTRAL_LOOK.hairColor),
  facial: pick(FACIALS, props.facial, NEUTRAL_LOOK.facial),
  hat: pick(HATS, props.hat, NEUTRAL_LOOK.hat),
  glasses: props.glasses === true || props.glasses === "true",
  outfit: pick(OUTFITS, props.outfit, NEUTRAL_LOOK.outfit),
  skin: typeof props.skin === "string" ? pick(SKINS, props.skin, "light") : "paper",
});

export const HIDES_HAIR_TOP: readonly Hat[] = ["cap", "kepi", "bicorne", "helmet", "top-hat", "beret", "turban", "wig"];

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
