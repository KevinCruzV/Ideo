export type CaptionWord = { w: string; from: number; to: number };
export type CaptionGroup = { words: CaptionWord[]; from: number; to: number };

export type TimelineItem = { el: string; at: number };

export type Segment = {
  kind: "hook" | "scene" | "outro";
  type?: string;
  from: number;
  to: number;
  props: Record<string, unknown>;
  items?: TimelineItem[];
  beats?: number[];
  break?: boolean;
  audio?: { kind: string; from: number; to: number; levels: number[] };
};

export type Chapter = { part: number; total: number; title: string; label: string };

export type Timeline = {
  mood?: "dark";
  paper?: string;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  lang: string;
  audio: string | null;
  watermark: string;
  chapter: Chapter;
  segments: Segment[];
  captions: CaptionGroup[];
};
