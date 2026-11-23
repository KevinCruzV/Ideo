import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { colors, fonts, onPaper, PaperColor } from "../theme";
import { useAccent } from "./accent";
import { num, str, suffixOf, variantOf } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { areaFor, FitBox } from "./FitBox";
import { enterFor } from "./timing";
import { useBeat } from "./beats";

const decimals = (n: number): number => {
  const s = String(n);
  const dot = s.indexOf(".");
  return dot < 0 ? 0 : Math.min(2, s.length - dot - 1);
};

export const formatCount = (value: number, places: number): string =>
  new Intl.NumberFormat("fr-FR", { minimumFractionDigits: places, maximumFractionDigits: places })
    .format(value)
    .replace(/[  ]/g, " ");

export const COUNTER_VARIANTS = 3;

export const Counter: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const beat = useBeat();
  const pulse = beat ? beat.wave : 0;
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
  const variant = variantOf(props.variant, COUNTER_VARIANTS);
  const disc = 660;
  const wide = BOX_W - 40;
  const numberFit = fitText(widest, { maxWidth: variant === 0 ? disc - 70 : wide - 120, maxLines: 1, max: variant === 0 ? 250 : 230, min: 60 });
  const numberIn = start !== 0 ? interpolate(frame, [-3, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : interpolate(frame - runAt, [0, 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const settle = interpolate(frame - runAt - runFor, [0, 4, 10], [1, 1.06, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const figure = (color: string) => (
    <span
      style={{
        fontFamily: variant === 2 ? fonts.brand : fonts.text,
        fontWeight: 800,
        fontSize: numberFit.size,
        lineHeight: 1,
        color,
        fontVariantNumeric: "tabular-nums",
        whiteSpace: "nowrap",
        opacity: numberIn,
        transform: `translateY(${(1 - numberIn) * 24}px) scale(${settle})`,
      }}
    >
      {shown}
    </span>
  );

  return (
    <Stage>
      <FitBox area={areaFor(areaTop(props) + 10, BOX_L, BOX_W)}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 50, width: BOX_W }}>
          {variant === 0 ? (
            <div style={{ position: "relative", width: disc, height: disc, transform: `scale(${1 + 0.11 * pulse}) rotate(${(beat && beat.index % 2 ? 3 : -3) * pulse}deg)` }}>
              <PaperShape kind="circle" color={accent} size={disc} seed="counter-disc" float={4} motion={{ dy: 0, spin: -8, from: 0.9 }}>
                {figure(onPaper[accent])}
              </PaperShape>
              <Picto name={props.picto} size={220} x={-80} y={-40} rotate={-10} />
            </div>
          ) : variant === 1 ? (
            <div style={{ position: "relative", width: wide, height: 380, transform: `scale(${1 + 0.08 * pulse}) rotate(${-2 + 2 * pulse}deg)` }}>
              <PaperShape kind="square" color="ink" size={1} w={wide} h={380} seed="counter-ticket" float={3} motion={{ dx: -160, dy: 0, spin: -6 }}>
                {figure(onPaper.ink)}
              </PaperShape>
              <PaperShape kind="circle" color={accent} size={90} x={-45} y={145} seed="counter-notch-a" shadow={false} />
              <PaperShape kind="circle" color={accent} size={90} x={wide - 45} y={145} seed="counter-notch-b" shadow={false} />
              <Picto name={props.picto} size={200} x={wide - 170} y={-120} rotate={12} />
            </div>
          ) : (
            <div style={{ position: "relative", width: wide, height: 520, transform: `scale(${1 + 0.08 * pulse})` }}>
              <PaperShape kind="square" color="cream" size={1} w={wide} h={520} rotate={1.5} seed="counter-board" float={2} motion={{ dy: 100, spin: 4 }}>
                <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 120, background: colors[accent as PaperColor] }} />
                <div style={{ position: "absolute", left: 0, right: 0, top: 120, bottom: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {figure(colors.ink)}
                </div>
              </PaperShape>
              <Picto name={props.picto} size={190} x={-60} y={-90} rotate={-12} />
            </div>
          )}
          <Strips lines={label.lines} size={label.size} enterAt={enterFor("label", items, from, to)} seed="counter-label" />
        </div>
      </FitBox>
    </Stage>
  );
};
