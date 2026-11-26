import React from "react";
import { colors, layout, shade } from "../theme";
import { hash, signed } from "./motion";

export const SHEET_LEFT = 34;
export const SHEET_RIGHT = layout.width - 34;
export const SHEET_TOP = layout.stageTop - 34;
export const SHEET_BOTTOM = layout.stageBottom + 14;
export const SHEET_TILT = 1.6;
export const TEAR_TEETH = 16;
export const TEAR_DEPTH = 2.2;
const SHEET_SHADOW = 14;

export const tornEdge = (seed: string, teeth = TEAR_TEETH, depth = TEAR_DEPTH): string => {
  const top = Array.from({ length: teeth + 1 }, (_, i) => {
    const x = (i / teeth) * 100 + (i > 0 && i < teeth ? signed(`${seed}:tx${i}`, 1.5) : 0);
    return `${x.toFixed(2)}% ${(hash(`${seed}:ty${i}`) * depth).toFixed(2)}%`;
  });
  const bottom = Array.from({ length: teeth + 1 }, (_, i) => {
    const x = 100 - (i / teeth) * 100 + (i > 0 && i < teeth ? signed(`${seed}:bx${i}`, 1.5) : 0);
    return `${x.toFixed(2)}% ${(100 - hash(`${seed}:by${i}`) * depth).toFixed(2)}%`;
  });
  return `polygon(${[...top, ...bottom].join(", ")})`;
};

export const sheetTilt = (index: number): number => (index % 2 === 0 ? -SHEET_TILT : SHEET_TILT);

const Tape: React.FC<{ x: number; y: number; rotate: number }> = ({ x, y, rotate }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: 200,
      height: 56,
      background: colors.cream,
      opacity: 0.78,
      transform: `rotate(${rotate}deg)`,
    }}
  />
);

export const Sheet: React.FC<{ index: number }> = ({ index }) => {
  const seed = `sheet-${index}`;
  const edge = tornEdge(seed);
  const width = SHEET_RIGHT - SHEET_LEFT;
  const height = SHEET_BOTTOM - SHEET_TOP;
  return (
    <div
      style={{
        position: "absolute",
        left: SHEET_LEFT,
        top: SHEET_TOP,
        width,
        height,
        transform: `rotate(${sheetTilt(index)}deg)`,
      }}
    >
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHEET_SHADOW * 0.7}px, ${SHEET_SHADOW}px)`, background: shade, clipPath: edge }} />
      <div style={{ position: "absolute", inset: 0, background: colors.cream, clipPath: edge }} />
      <Tape x={-30} y={-26} rotate={-14 + signed(`${seed}:ta`, 4)} />
      <Tape x={width - 170} y={-22} rotate={11 + signed(`${seed}:tb`, 4)} />
    </div>
  );
};
