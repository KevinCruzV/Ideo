import { TimelineItem } from "../types";

export const ENTER_FRAMES = 6;

export const enterFor = (el: string, items: TimelineItem[], from: number, to: number): number => {
  const item = items.find((i) => i.el === el);
  if (!item || !Number.isFinite(item.at)) return 0;
  const duration = Math.max(1, to - from);
  const latest = Math.max(0, duration - ENTER_FRAMES - 2);
  return Math.min(latest, Math.max(0, Math.round(item.at - from)));
};

export const stateTimes = (prefix: string, count: number, items: TimelineItem[], from: number, to: number): number[] => {
  const listed = items.some((i) => i.el.startsWith(`${prefix}.`));
  const duration = Math.max(1, to - from);
  return Array.from({ length: count }, (_, i) => {
    if (listed) return enterFor(`${prefix}.${i}`, items, from, to);
    return Math.round((i * duration) / Math.max(1, count));
  });
};

export const stateIndex = (times: number[], frame: number): number => {
  let index = 0;
  times.forEach((t, i) => {
    if (frame >= t) index = i;
  });
  return index;
};
