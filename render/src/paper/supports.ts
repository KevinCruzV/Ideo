import type { Segment } from "../types";

export const PAPERS = ["creme", "kraft", "journal", "millimetre", "album"] as const;
export type Paper = (typeof PAPERS)[number];
export type Support = Paper | "ticket" | "clipping" | "postit" | "none";

const MONEY = new Set(["€", "cts"]);
const PRICED = new Set(["counter", "shape-diagram"]);
const CLIPPED = new Set(["quote", "timeline"]);
const BARE = new Set(["stamp", "mascot"]);

export const paperOf = (value: unknown, dark: boolean): Paper =>
  PAPERS.includes(value as Paper) ? (value as Paper) : dark ? "journal" : "creme";

const wanted = (segment: Segment, first: boolean, paper: Paper): Support => {
  if (segment.kind !== "scene") return paper;
  const type = segment.type ?? "";
  if (PRICED.has(type) && MONEY.has(String(segment.props?.unit ?? ""))) return "ticket";
  if (CLIPPED.has(type)) return "clipping";
  if (BARE.has(type)) return "none";
  if (type === "key-title" && !first) return "postit";
  return paper;
};

export const supportsFor = (segments: Segment[], paper: Paper): Support[] => {
  const out: Support[] = [];
  let seenScene = false;
  for (const segment of segments) {
    const first = segment.kind === "scene" && !seenScene;
    if (segment.kind === "scene") seenScene = true;
    const support = wanted(segment, first, paper);
    out.push(support !== paper && out[out.length - 1] === support ? paper : support);
  }
  return out;
};

export const photoFrame = (paper: Paper): "polaroid" | "plain" => (paper === "album" ? "polaroid" : "plain");
