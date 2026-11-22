import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, fonts, onPaper, PaperColor, shade, SHADOW_X, SHADOW_Y } from "../theme";
import { cutEdge, drift, entry, EntryOptions, paperTransform, restTilt } from "./motion";

export type PaperStripProps = {
  text: string;
  color?: PaperColor;
  enterAt?: number;
  fontSize?: number;
  rotate?: number;
  seed?: string;
  float?: number;
  motion?: EntryOptions;
  weight?: number;
  family?: string;
  spacing?: number;
  style?: React.CSSProperties;
};

export const STRIP_LINE = 1.22;
export const STRIP_PAD_Y = 0.16;
export const STRIP_PAD_X = 0.3;

export const stripHeight = (fontSize: number): number => fontSize * (STRIP_LINE + STRIP_PAD_Y * 2.1);

export const PaperBacking: React.FC<{ color: PaperColor; seed: string; amount?: number }> = ({ color, seed, amount = 1.2 }) => {
  const edge = cutEdge(seed, amount);
  return (
    <>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X}px, ${SHADOW_Y}px)`, background: shade, clipPath: edge }} />
      <div style={{ position: "absolute", inset: 0, background: colors[color], clipPath: edge }} />
    </>
  );
};

export const PaperStrip: React.FC<PaperStripProps> = ({
  text,
  color = "cream",
  enterAt = 0,
  fontSize = 64,
  rotate,
  seed,
  float = 3.5,
  motion,
  weight = 800,
  family = fonts.text,
  spacing = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const key = seed ?? text;
  const tilt = rotate ?? restTilt(key, 1.6);
  const e = entry(frame, enterAt, { dy: fontSize * 0.45, spin: tilt > 0 ? 4 : -4, ...motion });
  const d = drift(key, frame, float, 0.6);

  return (
    <div
      style={{
        display: "inline-block",
        position: "relative",
        opacity: e.opacity,
        transform: paperTransform(e, d, tilt),
        ...style,
      }}
    >
      <PaperBacking color={color} seed={key} />
      <div
        style={{
          position: "relative",
          color: onPaper[color],
          fontFamily: family,
          fontWeight: weight,
          fontSize,
          letterSpacing: spacing,
          lineHeight: STRIP_LINE,
          padding: `${fontSize * STRIP_PAD_Y}px ${fontSize * STRIP_PAD_X}px ${fontSize * STRIP_PAD_Y * 1.1}px`,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </div>
  );
};
