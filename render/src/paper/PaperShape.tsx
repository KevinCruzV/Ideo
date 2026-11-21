import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, PaperColor, shade, SHADOW_X, SHADOW_Y } from "../theme";
import { cutCircle, cutEdge, cutPolygon, drift, entry, EntryOptions, paperTransform, SUPPORT_AT } from "./motion";

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
  seed?: string;
  float?: number;
  spin?: number;
  motion?: EntryOptions;
  origin?: string;
  shadow?: boolean;
  radius?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
};

const outline = (kind: ShapeKind, seed: string): string => {
  if (kind === "circle") return cutCircle(seed);
  if (kind === "triangle") return cutPolygon(seed, [[50, 1.5], [99, 98], [1, 98]], 0.8);
  if (kind === "diamond") return cutPolygon(seed, [[50, 1], [99, 50], [50, 99], [1, 50]], 0.8);
  if (kind === "arrow") return cutPolygon(seed, [[0, 32], [58, 32], [58, 2], [100, 50], [58, 98], [58, 68], [0, 68]], 0.8);
  return cutEdge(seed, kind === "strip" ? 1.4 : 0.9);
};

export const PaperCut: React.FC<{ kind: ShapeKind; color: PaperColor; seed: string; shadow?: boolean; radius?: string }> = ({
  kind,
  color,
  seed,
  shadow = true,
  radius,
}) => {
  const clip = radius ? undefined : outline(kind, seed);
  return (
    <>
      {shadow ? (
        <div
          style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X}px, ${SHADOW_Y}px)`, background: shade, clipPath: clip, borderRadius: radius }}
        />
      ) : null}
      <div style={{ position: "absolute", inset: 0, background: colors[color], clipPath: clip, borderRadius: radius }} />
    </>
  );
};

export const PaperShape: React.FC<PaperShapeProps> = ({
  kind,
  color,
  size,
  rotate = 0,
  enterAt = SUPPORT_AT,
  x = 0,
  y = 0,
  w,
  h,
  seed = `${kind}-${color}-${size}`,
  float = 3,
  spin = 0.4,
  motion,
  origin = "50% 50%",
  shadow = true,
  radius,
  style,
  children,
}) => {
  const frame = useCurrentFrame();
  const width = w ?? (kind === "strip" || kind === "arrow" ? size * 2.4 : size);
  const height = h ?? (kind === "strip" ? size * 0.5 : kind === "arrow" ? size * 0.9 : size);
  const e = entry(frame, enterAt, { dy: Math.min(60, height * 0.18), spin: rotate >= 0 ? 6 : -6, ...motion });
  const d = drift(seed, frame, float, spin);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width,
        height,
        opacity: e.opacity,
        transform: paperTransform(e, d, rotate),
        transformOrigin: origin,
        ...style,
      }}
    >
      <PaperCut kind={kind} color={color} seed={seed} shadow={shadow} radius={radius} />
      {children ? (
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>{children}</div>
      ) : null}
    </div>
  );
};
