import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { num, str, suffixOf } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { areaFor, FitBox } from "./FitBox";
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
  const unit = str(props.unit).slice(0, 4);
  const tailText = unit || suffix;
  const shown = `${formatCount(value, places)}${tailText ? `\u00a0${tailText}` : ""}`;
  const widest = `${formatCount(Math.abs(end) > Math.abs(start) ? end : start, places)}${tailText ? `\u00a0${tailText}` : ""}`;
  const label = fitText(str(props.label), { maxWidth: BOX_W, maxLines: 3, max: 82, min: 56, prefer: true });
  const disc = 660;
  const numberFit = fitText(widest, { maxWidth: disc - 70, maxLines: 1, max: 250, min: 60 });
  const numberIn = interpolate(frame - runAt, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const settle = interpolate(frame - runAt - runFor, [0, 4, 10], [1, 1.06, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <Stage>
      <FitBox area={areaFor(areaTop(props) + 10, BOX_L, BOX_W)}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 50, width: BOX_W }}>
          <div style={{ position: "relative", width: disc, height: disc }}>
            <PaperShape kind="circle" color={accent} size={disc} seed="counter-disc" float={4} motion={{ dy: 0, spin: -8, from: 0.9 }}>
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
            <Picto name={props.picto} size={220} x={-80} y={-40} rotate={-10} />
          </div>
          <Strips lines={label.lines} size={label.size} enterAt={enterFor("label", items, from, to)} seed="counter-label" />
        </div>
      </FitBox>
    </Stage>
  );
};
