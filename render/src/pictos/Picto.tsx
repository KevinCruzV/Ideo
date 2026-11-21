import React from "react";
import { useCurrentFrame } from "remotion";
import { drift, entry, EntryOptions, paperTransform, SUPPORT_AT } from "../paper/motion";
import { colors, shade } from "../theme";
import { pictoName, pictoPieces } from "./library";

export const PictoArt: React.FC<{ name: unknown; size: number; style?: React.CSSProperties }> = ({ name, size, style }) => {
  const key = pictoName(name);
  if (!key) return null;
  const pieces = pictoPieces(key);
  const off = Math.max(1.4, Math.min(2.4, 300 / size));
  return (
    <svg width={size} height={size} viewBox="-4 -4 108 108" style={{ display: "block", overflow: "visible", ...style }}>
      {pieces.map((p, i) => (
        <g key={i}>
          <path d={p.d} fill={shade} fillRule="evenodd" transform={`translate(${off} ${off * 1.35})`} />
          <path d={p.d} fill={colors[p.c]} fillRule="evenodd" />
        </g>
      ))}
    </svg>
  );
};

export type PictoProps = {
  name: unknown;
  size: number;
  x?: number;
  y?: number;
  enterAt?: number;
  rotate?: number;
  seed?: string;
  float?: number;
  motion?: EntryOptions;
  style?: React.CSSProperties;
};

export const Picto: React.FC<PictoProps> = ({ name, size, x, y, enterAt = SUPPORT_AT, rotate = 0, seed, float = 3, motion, style }) => {
  const frame = useCurrentFrame();
  if (!pictoName(name)) return null;
  const key = seed ?? `picto-${String(name)}`;
  const e = entry(frame, enterAt, { dy: 40, spin: rotate >= 0 ? 8 : -8, from: 0.9, ...motion });
  const d = drift(key, frame, float, 0.8);
  const placed: React.CSSProperties = x !== undefined || y !== undefined ? { position: "absolute", left: x ?? 0, top: y ?? 0 } : { position: "relative" };
  return (
    <div style={{ ...placed, width: size, height: size, opacity: e.opacity, transform: paperTransform(e, d, rotate), ...style }}>
      <PictoArt name={name} size={size} />
    </div>
  );
};
