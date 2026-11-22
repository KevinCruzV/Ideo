import { TimelineItem } from "../types";

export const str = (value: unknown, fallback = ""): string => {
  if (typeof value === "string") return value.replace(/\u2014/g, ",").replace(/\s+/g, " ").trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const o = value as Record<string, unknown>;
    for (const key of ["text", "label", "name", "value"]) {
      if (typeof o[key] === "string" || typeof o[key] === "number") return str(o[key], fallback);
    }
  }
  return fallback;
};

export const list = (value: unknown, max: number): unknown[] => {
  if (Array.isArray(value)) return value.slice(0, max);
  if (value === undefined || value === null || value === "") return [];
  return [value].slice(0, max);
};

export const strList = (value: unknown, max: number): string[] => {
  const source = typeof value === "string" ? value.split(/\s*[\n;|]\s*/) : list(value, max);
  return source.map((v) => str(v)).filter((v) => v.length > 0).slice(0, max);
};

export const num = (value: unknown): number | null => {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string") {
    const match = value.replace(/\s/g, "").replace(",", ".").match(/-?\d+(\.\d+)?/);
    return match ? Number(match[0]) : null;
  }
  return null;
};

export const unitList = (value: unknown, max: number): number[] => {
  const raw = list(value, max).map((v) => Math.max(0, num(v) ?? 0));
  const top = Math.max(0, ...raw);
  const scale = top > 1 ? top : 1;
  return raw.map((n) => Math.min(1, n / scale));
};

export const suffixOf = (value: unknown): string => {
  if (typeof value !== "string") return "";
  const match = value.trim().match(/^-?[\d\s.,]+(.*)$/);
  return match ? match[1].trim() : "";
};

export const cleanItems = (value: unknown): TimelineItem[] =>
  list(value, 64).flatMap((v) => {
    if (!v || typeof v !== "object") return [];
    const o = v as Record<string, unknown>;
    const at = num(o.at);
    return typeof o.el === "string" && at !== null ? [{ el: o.el, at }] : [];
  });

export const initials = (name: string): string => {
  const words = name
    .replace(/[^\p{L}\p{N}\s'-]/gu, " ")
    .split(/[\s'-]+/)
    .filter((w) => w.length > 0 && /\p{L}|\p{N}/u.test(w[0]));
  const significant = words.filter((w) => w[0] === w[0].toUpperCase());
  const picked = (significant.length > 0 ? significant : words).filter((_, i, a) => i === 0 || i === a.length - 1);
  const letters = picked.map((w) => w[0].toUpperCase()).join("");
  return letters.length > 0 ? letters.slice(0, 2) : "?";
};

export const FIRST_ITEM_MAX = 9;

export const earlyItems = (items: TimelineItem[], from: number): TimelineItem[] => {
  if (items.length === 0) return items;
  const first = Math.min(...items.map((i) => i.at));
  if (first - from <= FIRST_ITEM_MAX) return items;
  return items.map((i) => (i.at === first ? { ...i, at: from + FIRST_ITEM_MAX } : i));
};

export const photoSource = (value: unknown): string | null =>
  typeof value === "string" && /^[\w-]+\.(jpe?g|png|webp)$/i.test(value) ? value : null;
