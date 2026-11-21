import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { stepFrame } from "../paper/stopMotion";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { num, str, suffixOf } from "./coerce";
import { fitText } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_W } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const DISC = 620;

const decimals = (n: number): number => {
  const s = String(n);
  const dot = s.indexOf(".");
  return dot < 0 ? 0 : Math.min(2, s.length - dot - 1);
};

export const formatCount = (value: number, places: number): string =>
  new Intl.NumberFormat("fr-FR", { minimumFractionDigits: places, maximumFractionDigits: places })
    .format(value)
    .replace(/[  ]/g, " ");

export const Counter: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const end = num(props.to) ?? num(props.from) ?? 0;
  const start = num(props.from) ?? 0;
  const suffix = suffixOf(props.to) || suffixOf(props.from);
  const places = Math.max(decimals(start), decimals(end));
  const duration = Math.max(1, to - from);
  const runAt = enterFor("to", items, from, to);
  const runFor = Math.max(6, Math.round((duration - runAt) * 0.55));
  const progress = Math.min(1, Math.max(0, (stepFrame(frame) - runAt) / runFor));
  const eased = 1 - Math.pow(1 - progress, 2);
  const factor = Math.pow(10, places);
  const value = Math.round((start + (end - start) * eased) * factor) / factor;
  const shown = `${formatCount(value, places)}${suffix ? ` ${suffix}` : ""}`;
  const widest = `${formatCount(Math.abs(end) > Math.abs(start) ? end : start, places)}${suffix ? ` ${suffix}` : ""}`;
  const numberFit = fitText(widest, { maxWidth: DISC - 40, maxLines: 1, max: 230, min: 60 });
  const label = fitText(str(props.label), { maxWidth: 900, maxLines: 2, max: 76, min: 48 });

  return (
    <Stage>
      <PaperShape kind="square" color="cream" size={250} x={70} y={70} rotate={-10} seed="counter-back" />
      <PaperShape kind="circle" color={accent} size={DISC} x={(STAGE_W - DISC) / 2 + 30} y={60} seed="counter-disc" wobble={0.5}>
        <span
          style={{
            fontFamily: fonts.text,
            fontWeight: 800,
            fontSize: numberFit.size,
            lineHeight: 1,
            color: onPaper[accent],
            fontVariantNumeric: "tabular-nums",
            whiteSpace: "nowrap",
          }}
        >
          {shown}
        </span>
      </PaperShape>
      <div style={{ position: "absolute", left: 60, right: 60, top: 740, display: "flex", justifyContent: "center" }}>
        <Strips lines={label.lines} size={label.size} enterAt={enterFor("label", items, from, to)} seed="counter-label" />
      </div>
    </Stage>
  );
};
