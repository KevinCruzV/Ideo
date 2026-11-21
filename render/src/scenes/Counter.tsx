import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { num, str, suffixOf } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const decimals = (n: number): number => {
  const s = String(n);
  const dot = s.indexOf(".");
  return dot < 0 ? 0 : Math.min(2, s.length - dot - 1);
};

export const formatCount = (value: number, places: number): string =>
  new Intl.NumberFormat("fr-FR", { minimumFractionDigits: places, maximumFractionDigits: places })
    .format(value)
    .replace(/[  ]/g, " ");

export const Counter: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const end = num(props.to) ?? num(props.from) ?? 0;
  const start = num(props.from) ?? 0;
  const suffix = suffixOf(props.to) || suffixOf(props.from);
  const places = Math.max(decimals(start), decimals(end));
  const duration = Math.max(1, to - from);
  const runAt = enterFor("to", items, from, to);
  const runFor = Math.max(18, Math.min(60, Math.round((duration - runAt) * 0.5)));
  const progress = interpolate(frame - runAt, [0, runFor], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const eased = 1 - Math.pow(1 - progress, 3);
  const factor = Math.pow(10, places);
  const value = Math.round((start + (end - start) * eased) * factor) / factor;
  const shown = `${formatCount(value, places)}${suffix ? ` ${suffix}` : ""}`;
  const widest = `${formatCount(Math.abs(end) > Math.abs(start) ? end : start, places)}${suffix ? ` ${suffix}` : ""}`;
  const label = fitText(str(props.label), { maxWidth: BOX_W, maxLines: 2, max: 82, min: 48, prefer: true });
  const top = areaTop(props);
  const labelH = stripsHeight(label.lines.length, label.size);
  const disc = Math.min(660, STAGE_H - top - labelH - 60);
  const numberFit = fitText(widest, { maxWidth: disc - 70, maxLines: 1, max: 250, min: 60 });
  const total = disc + 50 + labelH;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);
  const numberIn = interpolate(frame - runAt, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const settle = interpolate(frame - runAt - runFor, [0, 4, 10], [1, 1.06, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <Stage>
      <PaperShape kind="circle" color={accent} size={disc} x={BOX_CX - disc / 2} y={y0} seed="counter-disc" float={4} motion={{ dy: 0, spin: -8, from: 0.9 }}>
        <span
          style={{
            fontFamily: fonts.text,
            fontWeight: 800,
            fontSize: numberFit.size,
            lineHeight: 1,
            color: onPaper[accent],
            fontVariantNumeric: "tabular-nums",
            whiteSpace: "nowrap",
            opacity: numberIn,
            transform: `translateY(${(1 - numberIn) * 24}px) scale(${settle})`,
          }}
        >
          {shown}
        </span>
      </PaperShape>
      <Picto name={props.picto} size={220} x={Math.max(BOX_L - 10, BOX_CX - disc / 2 - 60)} y={y0 - 30} rotate={-10} enterAt={3} />
      <div style={{ position: "absolute", left: BOX_L, width: BOX_W, top: y0 + disc + 50, display: "flex", justifyContent: "center" }}>
        <Strips lines={label.lines} size={label.size} enterAt={enterFor("label", items, from, to)} seed="counter-label" />
      </div>
    </Stage>
  );
};
