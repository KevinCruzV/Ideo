export const colors = {
  background: "#f4efe4",
  red: "#e2462c",
  yellow: "#f5bf2a",
  blue: "#2747c9",
  cream: "#fbf6ea",
  ink: "#1f1a14",
} as const;

export type PaperColor = "red" | "yellow" | "blue" | "cream" | "ink";

export const onPaper: Record<PaperColor, string> = {
  red: colors.cream,
  yellow: colors.ink,
  blue: colors.cream,
  cream: colors.ink,
  ink: colors.cream,
};

export const fonts = {
  text: "'Bricolage Grotesque', sans-serif",
  brand: "'Unbounded', sans-serif",
} as const;

export const shadow = "2px 3px 0 rgba(0,0,0,.22)";
export const shadowFilter = "drop-shadow(2px 3px 0 rgba(0,0,0,.22))";

export const layout = {
  width: 1080,
  height: 1920,
  marginTop: 80,
  marginSide: 48,
  captionBottom: 440,
  progressBottom: 250,
  progressHeight: 16,
  stageTop: 190,
  stageBottom: 1220,
} as const;

export type AccentColor = "red" | "yellow" | "blue";

export const accentCycle: readonly AccentColor[] = ["red", "yellow", "blue"];

export const accentForIndex = (index: number): AccentColor => {
  const i = Number.isFinite(index) ? Math.abs(Math.trunc(index)) : 0;
  return accentCycle[i % accentCycle.length];
};

export type AccentSpan = { from: number; to: number; accent: AccentColor };

export const accentAt = (spans: AccentSpan[], frame: number): AccentColor => {
  const span = spans.find((s) => frame >= s.from && frame < s.to);
  return span ? span.accent : accentCycle[0];
};
export const stripClip = "polygon(0 4%, 100% 0, 98% 100%, 2% 94%)";
