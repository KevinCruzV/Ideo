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

export const shade = "rgba(31,26,20,.24)";
export const shadow = `3px 4px 0 ${shade}`;
export const SHADOW_X = 3;
export const SHADOW_Y = 4;

export const layout = {
  width: 1080,
  height: 1920,
  marginTop: 72,
  marginSide: 56,
  safeRight: 130,
  contentLeft: 64,
  contentRight: 950,
  stageTop: 196,
  stageBottom: 1300,
  captionTop: 1336,
  captionBottom: 1480,
  progressTop: 1546,
  progressHeight: 12,
} as const;

export const content = {
  left: layout.contentLeft,
  right: layout.contentRight,
  width: layout.contentRight - layout.contentLeft,
  center: (layout.contentLeft + layout.contentRight) / 2,
} as const;

export type AccentColor = "red" | "yellow" | "blue";

export const accentCycle: readonly AccentColor[] = ["red", "yellow", "blue"];

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
