import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, PaperColor, shadow, shadowFilter, stripClip } from "../theme";
import { enterScale, jitter } from "./stopMotion";

export type ShapeKind = "circle" | "square" | "strip" | "arrow" | "triangle" | "diamond";

export type PaperShapeProps = {
  kind: ShapeKind;
  color: PaperColor;
  size: number;
  rotate?: number;
  enterAt?: number;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  radius?: string;
  seed?: string;
  wobble?: number;
  style?: React.CSSProperties;
  children?: React.ReactNode;
};

const arrowClip = "polygon(0 30%, 58% 30%, 58% 0, 100% 50%, 58% 100%, 58% 70%, 0 70%)";
const triangleClip = "polygon(50% 2%, 100% 96%, 0 100%)";
const diamondClip = "polygon(50% 0, 100% 50%, 50% 100%, 0 50%)";

const clips: Partial<Record<ShapeKind, string>> = {
  strip: stripClip,
  arrow: arrowClip,
  triangle: triangleClip,
  diamond: diamondClip,
};

export const PaperShape: React.FC<PaperShapeProps> = ({
  kind,
  color,
  size,
  rotate = 0,
  enterAt = 0,
  x = 0,
  y = 0,
  w,
  h,
  radius,
  seed,
  wobble = 0.8,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const scale = enterScale(frame, enterAt);
  const width = w ?? (kind === "strip" || kind === "arrow" ? size * 2.4 : size);
  const height = h ?? (kind === "strip" ? size * 0.5 : kind === "arrow" ? size * 0.9 : size);
  const clip = clips[kind];
  const angle = rotate + (seed ? jitter(seed, frame, wobble) : 0);

  const box: React.CSSProperties = {
    position: "relative",
    width,
    height,
    background: colors[color],
    borderRadius: radius ?? (kind === "circle" ? "50%" : 0),
    boxShadow: clip ? undefined : shadow,
    clipPath: clip,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
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
        transform: `rotate(${angle}deg) scale(${scale})`,
        filter: clip ? shadowFilter : undefined,
        ...style,
      }}
    >
      <div style={box}>{children}</div>
    </div>
  );
};
