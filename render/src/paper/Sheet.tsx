import React from "react";
import { colors, darkMode, layout, shade, Surface, surfaceFill } from "../theme";
import type { Support } from "./supports";
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

export const zigzagEdge = (teeth: number, depth: number): string => {
  const top = Array.from({ length: teeth * 2 + 1 }, (_, i) => `${((i / (teeth * 2)) * 100).toFixed(2)}% ${(i % 2 === 0 ? 0 : depth).toFixed(2)}%`);
  const bottom = Array.from({ length: teeth * 2 + 1 }, (_, i) => `${(100 - (i / (teeth * 2)) * 100).toFixed(2)}% ${(100 - (i % 2 === 0 ? 0 : depth)).toFixed(2)}%`);
  return `polygon(${[...top, ...bottom].join(", ")})`;
};

export const cutEdge = (seed: string): string => {
  const j = (k: string) => signed(`${seed}:${k}`, 0.8);
  return `polygon(${j("a")}% ${j("b")}%, ${100 + j("c")}% ${j("d")}%, ${100 + j("e")}% ${100 + j("f")}%, ${j("g")}% ${100 + j("h")}%)`;
};

const LINES = "repeating-linear-gradient(0deg, rgba(31,26,20,.10) 0 4px, transparent 4px 18px)";
const GRID =
  "repeating-linear-gradient(0deg, rgba(39,71,201,.22) 0 2px, transparent 2px 120px), repeating-linear-gradient(90deg, rgba(39,71,201,.22) 0 2px, transparent 2px 120px), repeating-linear-gradient(0deg, rgba(39,71,201,.10) 0 1px, transparent 1px 24px), repeating-linear-gradient(90deg, rgba(39,71,201,.10) 0 1px, transparent 1px 24px)";

const Columns: React.FC = () => (
  <div style={{ position: "absolute", inset: "70px 60px", display: "flex", gap: 40, opacity: 0.6 }}>
    {[0, 1, 2].map((i) => (
      <div key={`col-${i}`} style={{ flex: 1, backgroundImage: LINES }} />
    ))}
  </div>
);

const Fold: React.FC = () => (
  <div
    style={{
      position: "absolute",
      right: 0,
      bottom: 0,
      width: 120,
      height: 120,
      background: `linear-gradient(135deg, transparent 50%, ${shade} 50%)`,
      clipPath: "polygon(100% 0, 100% 100%, 0 100%)",
    }}
  />
);

const Pin: React.FC<{ x: number }> = ({ x }) => (
  <div style={{ position: "absolute", left: x - 22, top: -14, width: 44, height: 44, borderRadius: 22, background: colors.red, boxShadow: `3px 4px 0 ${shade}` }} />
);

const edgeFor = (support: Surface, seed: string): string =>
  support === "ticket" ? zigzagEdge(28, 1.2) : support === "clipping" ? cutEdge(seed) : support === "postit" ? "none" : tornEdge(seed);

export const Sheet: React.FC<{ index: number; support?: Support }> = ({ index, support = "creme" }) => {
  if (support === "none") return null;
  const seed = `sheet-${index}`;
  const edge = edgeFor(support, seed);
  const width = SHEET_RIGHT - SHEET_LEFT;
  const height = SHEET_BOTTOM - SHEET_TOP;
  const fill = surfaceFill(support);
  const texture = support === "millimetre" ? GRID : undefined;
  const tilt = support === "postit" ? sheetTilt(index) * 1.8 : sheetTilt(index);
  const taped = support !== "ticket" && support !== "postit";
  return (
    <div style={{ position: "absolute", left: SHEET_LEFT, top: SHEET_TOP, width, height, transform: `rotate(${tilt}deg)` }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHEET_SHADOW * 0.7}px, ${SHEET_SHADOW}px)`, background: shade, clipPath: edge }} />
      <div style={{ position: "absolute", inset: 0, background: fill, backgroundImage: texture, clipPath: edge }}>
        {support === "journal" || support === "clipping" ? <Columns /> : null}
        {support === "postit" && !darkMode ? <Fold /> : null}
      </div>
      {support === "postit" && darkMode ? <Pin x={width / 2} /> : null}
      {taped && support !== "clipping" ? <Tape x={-30} y={-26} rotate={-14 + signed(`${seed}:ta`, 4)} /> : null}
      {taped ? <Tape x={width - 170} y={-22} rotate={11 + signed(`${seed}:tb`, 4)} /> : null}
    </div>
  );
};
