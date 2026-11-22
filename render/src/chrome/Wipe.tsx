import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { PaperCut } from "../paper/PaperShape";
import { layout, PaperColor } from "../theme";

export const WIPE_BEFORE = 7;
export const WIPE_AFTER = 2;
export const WIPE_FRAMES = WIPE_BEFORE + WIPE_AFTER;
const SHEET_W = 1500;
const SHEET_H = 2400;
const TRAVEL = layout.width / 2 + SHEET_W / 2 + 260;

const easeIn = (t: number) => t * t;
const easeOut = (t: number) => 1 - (1 - t) * (1 - t);

export const wipeOffset = (frame: number): number => {
  if (frame <= WIPE_BEFORE) {
    const t = easeIn(interpolate(frame, [0, WIPE_BEFORE], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
    return TRAVEL * (1 - t);
  }
  const t = easeOut(interpolate(frame, [WIPE_BEFORE, WIPE_FRAMES], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  return -TRAVEL * t;
};

export const Wipe: React.FC<{ color: PaperColor; seed: string }> = ({ color, seed }) => {
  const frame = useCurrentFrame();
  const x = wipeOffset(frame);
  return (
    <div
      style={{
        position: "absolute",
        left: layout.width / 2 - SHEET_W / 2 + x,
        top: layout.height / 2 - SHEET_H / 2,
        width: SHEET_W,
        height: SHEET_H,
        transform: "rotate(-9deg)",
      }}
    >
      <PaperCut kind="square" color={color} seed={seed} />
    </div>
  );
};
