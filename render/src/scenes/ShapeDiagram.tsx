import React from "react";
import { PaperShape, ShapeKind } from "../paper/PaperShape";
import { useAccent } from "./accent";
import { str, strList, unitList } from "./coerce";
import { Fit, fitText, textWidth } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H, STAGE_W } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const ROW_W = 940;
const GAP = 30;
const MAX = 400;
const BAR_H = 620;
const TILTS = [0, 9, -6, 4, -8, 6, -3, 7];

type Mode = "circle" | "square" | "triangle" | "bar";

const modeOf = (value: unknown): Mode => {
  const key = str(value).toLowerCase();
  if (["square", "carre", "carré"].includes(key)) return "square";
  if (key === "triangle") return "triangle";
  if (["bar", "bars", "strip", "barre", "column"].includes(key)) return "bar";
  return "circle";
};

export const sizesFor = (values: number[], rowWidth: number, gap: number, max: number): number[] => {
  const visible = values.map((v) => Math.max(0.05, v));
  const total = visible.reduce((a, b) => a + b, 0);
  const room = rowWidth - gap * Math.max(0, values.length - 1);
  const unit = Math.min(max, total > 0 ? room / total : max);
  return visible.map((v) => v * unit);
};

export const ShapeDiagram: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const mode = modeOf(props.shape);
  const values = unitList(props.values, 8);
  const shown = values.length > 0 ? values : [1];
  const labels = strList(props.labels, 8);
  const bar = mode === "bar";
  const barW = Math.min(150, (ROW_W - GAP * (shown.length - 1)) / shown.length);
  const sizes = bar ? shown.map(() => barW) : sizesFor(shown, ROW_W, GAP, MAX);
  const heights = bar ? shown.map((v) => Math.max(18, v * BAR_H)) : sizes;
  const rowW = sizes.reduce((a, b) => a + b, 0) + GAP * (shown.length - 1);
  const tallest = Math.max(...heights);
  const perShape = labels.length === shown.length;
  const labelMax = perShape && shown.length > 3 ? 46 : 60;
  const labelBlock = labels.length > 0 ? (perShape ? 260 : 150) : 0;
  const baseline = (STAGE_H - tallest - labelBlock) / 2 + tallest;
  const left0 = (STAGE_W - rowW) / 2;
  const labelFits: Fit[] = perShape
    ? labels.map((label) => fitText(label, { maxWidth: 320, maxLines: 2, max: labelMax, min: 40 }))
    : [];
  const widths = labelFits.map((f) => Math.max(...f.lines.map((l) => textWidth(l, f.size)), 0) + f.size * 0.6);
  const labelRow = Math.max(0, ...labelFits.map((f) => f.lines.length * f.size * 1.3)) + 16;
  const kind: ShapeKind = mode === "bar" ? "square" : mode;
  let cursor = left0;
  const placed = shown.map((_, i) => {
    const x = cursor;
    cursor += sizes[i] + GAP;
    return { x, w: sizes[i], h: heights[i] };
  });

  const centers = placed.map((p) => Math.min(STAGE_W - 60, Math.max(60, p.x + p.w / 2)));
  const stagger = centers.some((c, i) => i > 0 && c - centers[i - 1] < (widths[i] + widths[i - 1]) / 2 + 16);

  return (
    <Stage>
      {placed.map((p, i) => (
        <PaperShape
          key={`shape-${i}`}
          kind={kind}
          color={accent}
          size={p.w}
          w={p.w}
          h={p.h}
          x={p.x}
          y={baseline - p.h}
          rotate={bar ? TILTS[i % TILTS.length] * 0.2 : TILTS[i % TILTS.length]}
          enterAt={enterFor(`values.${i}`, items, from, to)}
          seed={`sd-${i}`}
          style={{ transformOrigin: "50% 100%" }}
        />
      ))}
      {perShape
        ? labelFits.map((fit, i) => {
            const center = centers[i];
            return (
              <div
                key={`label-${i}`}
                style={{
                  position: "absolute",
                  top: baseline + 40 + (stagger && i % 2 === 1 ? labelRow : 0),
                  left: center - 160,
                  width: 320,
                  display: "flex",
                  justifyContent: "center",
                }}
              >
                <Strips lines={fit.lines} size={fit.size} enterAt={enterFor(`labels.${i}`, items, from, to)} seed={`sd-label-${i}`} gap={6} />
              </div>
            );
          })
        : (
          <div
            style={{
              position: "absolute",
              top: baseline + 40,
              left: Math.max(48, left0 - 20),
              right: Math.max(48, STAGE_W - left0 - rowW - 20),
              display: "flex",
              justifyContent: labels.length === 1 ? "center" : "space-between",
              alignItems: "flex-start",
            }}
          >
            {labels.map((label, i) => {
              const fit = fitText(label, { maxWidth: 940 / Math.max(1, labels.length), maxLines: 2, max: 64, min: 40 });
              return (
                <Strips
                  key={`label-${i}`}
                  lines={fit.lines}
                  size={fit.size}
                  enterAt={enterFor(`labels.${i}`, items, from, to)}
                  seed={`sd-label-${i}`}
                  tilt={i % 2 === 0 ? -2 : 2}
                  gap={6}
                />
              );
            })}
          </div>
        )}
    </Stage>
  );
};
