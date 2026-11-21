import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, PaperColor, shadow, shadowFilter, stripClip } from "../theme";
import { stepFrame } from "./stopMotion";

export type ShapeKind = "circle" | "square" | "strip" | "arrow";

export type PaperShapeProps = {
  kind: ShapeKind;
  color: PaperColor;
  size: number;
  rotate?: number;
  enterAt?: number;
  x?: number;
  y?: number;
  style?: React.CSSProperties;
};

const ENTER_SCALES = [0.4, 0.75, 1];
const STEP_FRAMES = 2.5;

export const enterScale = (frame: number, enterAt: number): number => {
  const local = frame - enterAt;
  if (local < 0) return 0;
  const index = Math.round(stepFrame(local) / STEP_FRAMES);
  return ENTER_SCALES[Math.min(index, ENTER_SCALES.length - 1)];
};

const arrowClip = "polygon(0 30%, 58% 30%, 58% 0, 100% 50%, 58% 100%, 58% 70%, 0 70%)";

export const PaperShape: React.FC<PaperShapeProps> = ({
  kind,
  color,
  size,
  rotate = 0,
  enterAt = 0,
  x = 0,
  y = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const scale = enterScale(frame, enterAt);
  const width = kind === "strip" || kind === "arrow" ? size * 2.4 : size;
  const height = kind === "strip" ? size * 0.5 : kind === "arrow" ? size * 0.9 : size;
  const fill = colors[color];
  const clipped = kind === "strip" || kind === "arrow";

  const box: React.CSSProperties = {
    width,
    height,
    background: fill,
    borderRadius: kind === "circle" ? "50%" : 0,
    boxShadow: clipped ? undefined : shadow,
    clipPath: kind === "strip" ? stripClip : kind === "arrow" ? arrowClip : undefined,
  };

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width,
        height,
        opacity: scale === 0 ? 0 : 1,
        transform: `rotate(${rotate}deg) scale(${scale})`,
        filter: clipped ? shadowFilter : undefined,
        ...style,
      }}
    >
      <div style={box} />
    </div>
  );
};
