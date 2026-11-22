import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape, ShapeKind } from "../paper/PaperShape";
import { PaperColor } from "../theme";

export type BackdropProps = {
  kind?: ShapeKind;
  color: PaperColor;
  size: number;
  cx: number;
  cy: number;
  w?: number;
  h?: number;
  rotate?: number;
  seed: string;
  turn?: number;
};

export const Backdrop: React.FC<BackdropProps> = ({ kind = "circle", color, size, cx, cy, w, h, rotate = 0, seed, turn = 4 }) => {
  const frame = useCurrentFrame();
  const width = w ?? size;
  const height = h ?? size;
  const breathe = 1 + 0.025 * Math.sin((frame / 30) * 0.9);
  return (
    <PaperShape
      kind={kind}
      color={color}
      size={size}
      w={width}
      h={height}
      x={cx - width / 2}
      y={cy - height / 2}
      rotate={rotate + (turn * frame) / 300}
      seed={seed}
      float={6}
      spin={0.6}
      motion={{ dy: 0, dx: 0, spin: -10, from: 0.9 }}
      style={{ scale: String(breathe) }}
    />
  );
};
