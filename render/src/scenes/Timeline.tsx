import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { useAccent } from "./accent";
import { list, num, str } from "./coerce";
import { fitText } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const AXIS_X = 170;
const TOP = 70;
const BOTTOM = STAGE_H - 70;

type Mark = { at: string; label: string; value: number | null };

export const placeMarks = (
  values: (number | null)[],
  start: number | null,
  end: number | null,
  top: number,
  bottom: number,
  gap: number,
  edge = gap,
): number[] => {
  const n = values.length;
  if (n === 0) return [];
  const innerTop = top + edge;
  const innerBottom = bottom - edge;
  const even = values.map((_, i) => (n === 1 ? (innerTop + innerBottom) / 2 : innerTop + ((innerBottom - innerTop) * i) / (n - 1)));
  if (start === null || end === null || start === end || values.some((v) => v === null)) return even;
  const ys = values.map((v) => top + ((bottom - top) * ((v as number) - start)) / (end - start));
  const ordered = ys.every((y, i) => i === 0 || y >= ys[i - 1]);
  if (!ordered) return even;
  const placed = ys.map((y) => Math.min(innerBottom, Math.max(innerTop, y)));
  for (let i = 1; i < n; i++) placed[i] = Math.max(placed[i], placed[i - 1] + gap);
  for (let i = n - 2; i >= 0; i--) placed[i] = Math.min(placed[i], placed[i + 1] - gap);
  return placed[0] < innerTop - 1 || placed[n - 1] > innerBottom + 1 ? even : placed;
};

export const Timeline: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const startText = str(props.start);
  const endText = str(props.end);
  const marks: Mark[] = list(props.marks, 5).map((m) => {
    const o = m && typeof m === "object" ? (m as Record<string, unknown>) : { label: m };
    const at = str(o.at);
    return { at, label: str(o.label) || at, value: num(o.at) };
  });
  const labelMax = marks.length <= 3 ? 60 : 52;
  const fits = marks.map((mark) => {
    const text = mark.at && mark.label !== mark.at ? `${mark.at} · ${mark.label}` : mark.label;
    return fitText(text, { maxWidth: 800, maxLines: 2, max: labelMax, min: 44 });
  });
  const heights = fits.map((f) => f.lines.length * f.size * 1.3);
  const gap = Math.max(110, ...heights.map((h) => h + 26));
  const ys = placeMarks(marks.map((m) => m.value), num(props.start), num(props.end), TOP, BOTTOM, gap, Math.max(100, gap * 0.6));
  const endFit = fitText(endText, { maxWidth: 760, maxLines: 1, max: 64, min: 44 });
  const startFit = fitText(startText, { maxWidth: 760, maxLines: 1, max: 64, min: 44 });

  return (
    <Stage>
      <PaperShape kind="square" color="cream" size={1} w={34} h={BOTTOM - TOP} x={AXIS_X - 17} y={TOP} rotate={0.6} seed="tl-axis" wobble={0.2} />
      <PaperShape kind="square" color="ink" size={64} x={AXIS_X - 32} y={TOP - 32} rotate={8} seed="tl-start" />
      <PaperShape kind="square" color="ink" size={64} x={AXIS_X - 32} y={BOTTOM - 32} rotate={-6} seed="tl-end" />
      <div style={{ position: "absolute", left: AXIS_X + 70, top: TOP - startFit.size * 0.7 }}>
        <Strips lines={startFit.lines} size={startFit.size} color="ink" align="flex-start" seed="tl-start-label" />
      </div>
      <div style={{ position: "absolute", left: AXIS_X + 70, top: BOTTOM - endFit.size * 0.7 }}>
        <Strips lines={endFit.lines} size={endFit.size} color="ink" align="flex-start" seed="tl-end-label" />
      </div>
      {marks.map((_, i) => {
        const at = enterFor(`marks.${i}`, items, from, to);
        const fit = fits[i];
        const y = ys[i];
        const textH = heights[i];
        return (
          <React.Fragment key={`mark-${i}`}>
            <PaperShape kind="circle" color={accent} size={76} x={AXIS_X - 38} y={y - 38} enterAt={at} seed={`tl-dot-${i}`} />
            <div style={{ position: "absolute", left: AXIS_X + 70, top: y - textH / 2 }}>
              <Strips lines={fit.lines} size={fit.size} enterAt={at + 1} align="flex-start" seed={`tl-mark-${i}`} gap={6} />
            </div>
          </React.Fragment>
        );
      })}
    </Stage>
  );
};
