import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { useAccent } from "./accent";
import { list, str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_R, Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";
import { stripHeight } from "../paper/PaperStrip";

const AXIS_X = BOX_L + 74;
const LABEL_X = AXIS_X + 76;
const LABEL_W = BOX_R - LABEL_X;

type Mark = { at: string; label: string };

export const placeMarks = (count: number, top: number, bottom: number, edgeTop: number, edgeBottom = edgeTop): number[] => {
  if (count === 0) return [];
  const innerTop = top + edgeTop;
  const innerBottom = bottom - edgeBottom;
  return Array.from({ length: count }, (_, i) => (count === 1 ? (innerTop + innerBottom) / 2 : innerTop + ((innerBottom - innerTop) * i) / (count - 1)));
};

export const Timeline: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const startText = str(props.start);
  const endText = str(props.end);
  const marks: Mark[] = list(props.marks, 5).map((m) => {
    const o = m && typeof m === "object" ? (m as Record<string, unknown>) : { label: m };
    const at = str(o.at);
    return { at, label: str(o.label) || at };
  });
  const area = areaTop(props);
  const hasPicto = pictoName(props.picto) !== null;
  const capH = hasPicto ? 150 : 64;
  const TOP = area + 40 + capH / 2;
  const BOTTOM = STAGE_H - 50;
  const labelMax = marks.length <= 3 ? 64 : 56;
  const dates = marks.map((mark) => (mark.at && mark.label !== mark.at ? fitText(mark.at, { maxWidth: LABEL_W, maxLines: 1, max: 44, min: 34 }) : null));
  const fits = marks.map((mark) => fitText(mark.label, { maxWidth: LABEL_W, maxLines: 2, max: labelMax, min: 44, prefer: true }));
  const dateH = (i: number) => (dates[i] ? stripHeight(dates[i]!.size) + 4 : 0);
  const heights = fits.map((f, i) => dateH(i) + f.lines.length * stripHeight(f.size) + (f.lines.length - 1) * 6);
  const endFit = fitText(endText, { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 36 });
  const startFit = fitText(startText, { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 36 });
  const lead = (i: number) => (dates[i] ? dateH(i) / 2 : heights[i] / 2);
  const startH = startFit.lines.length ? stripHeight(startFit.size) : capH;
  const endH = endFit.lines.length ? stripHeight(endFit.size) : 64;
  const last = marks.length - 1;
  const ys = placeMarks(
    marks.length,
    TOP,
    BOTTOM,
    marks.length ? Math.max(capH / 2 + 50, startH / 2 + lead(0) + 30) : 0,
    marks.length ? Math.max(70, endH / 2 + heights[last] - lead(last) + 30) : 0,
  );

  return (
    <Stage>
      <PaperShape kind="square" color="ink" size={1} w={22} h={BOTTOM - TOP} x={AXIS_X - 11} y={TOP} seed="tl-axis" float={0.8} spin={0.1} motion={{ dy: 0, spin: 0, from: 0.96 }} />
      {hasPicto ? (
        <Picto name={props.picto} size={capH} x={AXIS_X - capH / 2} y={TOP - capH / 2 - 10} rotate={-6} />
      ) : (
        <PaperShape kind="square" color="ink" size={capH} x={AXIS_X - capH / 2} y={TOP - capH / 2} rotate={8} seed="tl-start" />
      )}
      <PaperShape kind="square" color="ink" size={64} x={AXIS_X - 32} y={BOTTOM - 32} rotate={-6} seed="tl-end" />
      {startFit.lines.length ? (
        <div style={{ position: "absolute", left: LABEL_X + (hasPicto ? 20 : 0), top: TOP - stripHeight(startFit.size) / 2 }}>
          <Strips lines={startFit.lines} size={startFit.size} color="ink" align="flex-start" seed="tl-start-label" />
        </div>
      ) : null}
      {endFit.lines.length ? (
        <div style={{ position: "absolute", left: LABEL_X, top: BOTTOM - stripHeight(endFit.size) / 2 }}>
          <Strips lines={endFit.lines} size={endFit.size} color="ink" align="flex-start" seed="tl-end-label" />
        </div>
      ) : null}
      {marks.map((_, i) => {
        const at = enterFor(`marks.${i}`, items, from, to);
        const fit = fits[i];
        const y = ys[i];
        return (
          <React.Fragment key={`mark-${i}`}>
            <PaperShape kind="circle" color={accent} size={70} x={AXIS_X - 35} y={y - 35} enterAt={at} seed={`tl-dot-${i}`} float={1.5} motion={{ dy: 0, spin: 0, from: 0.9 }} />
            <div style={{ position: "absolute", left: LABEL_X, top: y - lead(i), display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
              {dates[i] ? (
                <Strips lines={dates[i]!.lines} size={dates[i]!.size} color={accent} enterAt={at + 1} align="flex-start" seed={`tl-date-${i}`} motion={{ dx: -30, dy: 0 }} />
              ) : null}
              <Strips lines={fit.lines} size={fit.size} enterAt={at + 3} align="flex-start" seed={`tl-mark-${i}`} gap={6} motion={{ dx: -40, dy: 0 }} />
            </div>
          </React.Fragment>
        );
      })}
    </Stage>
  );
};
