import React from "react";
import { PaperStrip, stripHeight } from "../paper/PaperStrip";
import { EntryOptions, restTilt } from "../paper/motion";
import { PaperColor } from "../theme";

export type StripsProps = {
  lines: string[];
  size: number;
  color?: PaperColor;
  enterAt?: number;
  stagger?: number;
  align?: "flex-start" | "center" | "flex-end";
  seed: string;
  tilt?: number;
  gap?: number;
  motion?: EntryOptions;
  style?: React.CSSProperties;
};

export const stripsGap = (size: number): number => Math.round(size * 0.16);

export const stripsHeight = (count: number, size: number, gap = stripsGap(size)): number =>
  count <= 0 ? 0 : count * stripHeight(size) + (count - 1) * gap;

export const Strips: React.FC<StripsProps> = ({
  lines,
  size,
  color = "cream",
  enterAt = 0,
  stagger = 3,
  align = "center",
  seed,
  tilt = 0,
  gap,
  motion,
  style,
}) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: align,
      gap: gap ?? stripsGap(size),
      ...style,
    }}
  >
    {lines.map((line, i) => (
      <PaperStrip
        key={`${seed}-${i}`}
        text={line}
        color={color}
        fontSize={size}
        enterAt={enterAt + i * stagger}
        rotate={tilt + restTilt(`${seed}-${i}`, 1.4)}
        seed={`${seed}-${i}`}
        motion={motion}
      />
    ))}
  </div>
);
