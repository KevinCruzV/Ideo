import type { Support } from "./paper/supports";
export type Mood = "dark";
export type Palette = {
  background: string;
  red: string;
  yellow: string;
  blue: string;
  cream: string;
  ink: string;
  fg: string;
  track: string;
};

export type PaperColor = "red" | "yellow" | "blue" | "cream" | "ink";

const LIGHT: Palette = {
  background: "#f4efe4",
  red: "#e2462c",
  yellow: "#f5bf2a",
  blue: "#2747c9",
  cream: "#fbf6ea",
  ink: "#1f1a14",
  fg: "#1f1a14",
  track: "rgba(31,26,20,.16)",
};

const DARK: Palette = {
  background: "#252932",
  red: "#a82a22",
  yellow: "#c99a1a",
  blue: "#3a5aa8",
  cream: "#d3ccba",
  ink: "#0e0c09",
  fg: "#efe8d8",
  track: "rgba(239,232,216,.2)",
};

const LIGHT_ON: Record<PaperColor, string> = { red: "#fbf6ea", yellow: "#1f1a14", blue: "#fbf6ea", cream: "#1f1a14", ink: "#fbf6ea" };
const DARK_ON: Record<PaperColor, string> = { red: "#fbf6ea", yellow: "#14110d", blue: "#fbf6ea", cream: "#1a1612", ink: "#efe8d8" };

export const palettes: Record<"light" | Mood, { colors: Palette; onPaper: Record<PaperColor, string>; shade: string }> = {
  light: { colors: LIGHT, onPaper: LIGHT_ON, shade: "rgba(31,26,20,.24)" },
  dark: { colors: DARK, onPaper: DARK_ON, shade: "rgba(0,0,0,.5)" },
};

export const colors: Palette = { ...LIGHT };
export const onPaper: Record<PaperColor, string> = { ...LIGHT_ON };
export let shade = palettes.light.shade;
export let dimmed = 0.38;
export let shadow = `3px 4px 0 ${shade}`;
export let darkMode = false;
export const SHADOW_X = 3;
export const SHADOW_Y = 4;

export const moodOf = (value: unknown): Mood | undefined => (value === "dark" ? "dark" : undefined);

export const setMood = (mood?: Mood): void => {
  const palette = palettes[mood ?? "light"];
  Object.assign(colors, palette.colors);
  Object.assign(onPaper, palette.onPaper);
  shade = palette.shade;
  dimmed = mood === "dark" ? 0.55 : 0.38;
  darkMode = mood === "dark";
  ground = GROUNDS[mood ?? "light"];
  shadow = `${SHADOW_X}px ${SHADOW_Y}px 0 ${shade}`;
};

export const fonts = {
  text: "'Bricolage Grotesque', sans-serif",
  brand: "'Unbounded', sans-serif",
} as const;

export const BRAND_WIDE = 1.3;


export const layout = {
  width: 1080,
  height: 1920,
  marginTop: 244,
  marginSide: 130,
  safeScale: 0.76,
  chromeScale: 0.82,
  safeLeft: 130,
  safeRight: 220,
  safeCenterX: 490,
  contentLeft: 64,
  contentRight: 950,
  stageTop: 244,
  stageBottom: 1348,
  captionTop: 1336,
  captionBottom: 1480,
  progressTop: 1546,
  progressHeight: 12,
} as const;

export const safeWindow = { left: layout.safeLeft, right: layout.width - layout.safeRight } as const;

export const visibleStageTop =
  (layout.stageTop + layout.stageBottom) / 2 - ((layout.stageBottom - layout.stageTop) / 2) * layout.safeScale;

export const content = {
  left: layout.contentLeft,
  right: layout.contentRight,
  width: layout.contentRight - layout.contentLeft,
  center: (layout.contentLeft + layout.contentRight) / 2,
} as const;

export type AccentColor = "red" | "yellow" | "blue";

export const accentCycle: readonly AccentColor[] = ["red", "yellow", "blue"];

export const GROUNDS: Record<"light" | Mood, { toward: PaperColor; amount: number }> = {
  light: { toward: "cream", amount: 0.15 },
  dark: { toward: "ink", amount: 0.35 },
};
let ground = GROUNDS.light;

const channels = (hex: string): number[] => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

export const mixHex = (a: string, b: string, t: number): string =>
  `#${channels(a)
    .map((v, i) => Math.round(v + (channels(b)[i] - v) * t).toString(16).padStart(2, "0"))
    .join("")}`;

export const groundOf = (accent: AccentColor): string => mixHex(colors[accent], colors[ground.toward], ground.amount);

export const nextAccent = (accent: AccentColor): AccentColor => accentCycle[(accentCycle.indexOf(accent) + 1) % accentCycle.length];

export const accentForIndex = (index: number): AccentColor => {
  const i = Number.isFinite(index) ? Math.abs(Math.trunc(index)) : 0;
  return accentCycle[i % accentCycle.length];
};

export const segmentAccent = (index: number, sceneType?: string): AccentColor => {
  const accent = accentForIndex(index);
  return sceneType === "mascot" && accent === "blue" ? "red" : accent;
};

export type AccentSpan = { from: number; to: number; accent: AccentColor };

export const accentAt = (spans: AccentSpan[], frame: number): AccentColor => {
  const span = spans.find((s) => frame >= s.from && frame < s.to);
  return span ? span.accent : accentCycle[0];
};

export type Surface = Exclude<Support, "none">;

const LIGHT_FILLS: Record<Surface, string> = {
  creme: "#fbf6ea",
  kraft: "#c9a37a",
  journal: "#e6e2d8",
  millimetre: "#f7f8f2",
  album: "#efe3c4",
  ticket: "#fefdf9",
  clipping: "#e6e2d8",
  postit: "#f7d65a",
};

const DARK_FILLS: Record<Surface, string> = {
  creme: "#d3ccba",
  kraft: "#a88a68",
  journal: "#c4c0b6",
  millimetre: "#cfd1ca",
  album: "#cbbfa2",
  ticket: "#d9d7d0",
  clipping: "#c4c0b6",
  postit: "#b9b4a8",
};

const withInk = (fills: Record<Surface, string>, ink: string) =>
  Object.fromEntries(Object.entries(fills).map(([k, fill]) => [k, { fill, ink }])) as Record<Surface, { fill: string; ink: string }>;

export const PAPER_COLORS: Record<"light" | "dark", Record<Surface, { fill: string; ink: string }>> = {
  light: withInk(LIGHT_FILLS, LIGHT_ON.cream),
  dark: withInk(DARK_FILLS, DARK_ON.cream),
};

export const surfaceFill = (support: Surface): string => PAPER_COLORS[darkMode ? "dark" : "light"][support].fill;
