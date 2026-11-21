import React from "react";
import { PaperStrip } from "../paper/PaperStrip";
import { PaperColor } from "../theme";

const TILTS = [-2.2, 1.6, -1.2, 2, -1.8, 1.2];

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
  style?: React.CSSProperties;
};

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
  style,
}) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: align,
      gap: gap ?? Math.round(size * 0.14),
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
        rotate={tilt + TILTS[(i + seed.length) % TILTS.length]}
        seed={`${seed}-${i}`}
      />
    ))}
  </div>
);
