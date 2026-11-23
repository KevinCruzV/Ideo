import React from "react";
import { useCurrentFrame } from "remotion";
import { drift, entry, EntryOptions, paperTransform, SUPPORT_AT } from "../paper/motion";
import { colors, PaperColor, shade } from "../theme";
import { Beat, useBeat } from "../scenes/beats";
import { FlagArt } from "./Flag";
import { flagCode } from "./flags";
import { pictoName, pictoPieces } from "./library";

export const hasVisual = (value: unknown): boolean => pictoName(value) !== null || flagCode(value) !== null;

export const pictoColors = (value: unknown): PaperColor[] => {
  const key = pictoName(value);
  return key ? [...new Set(pictoPieces(key).map((p) => p.c))] : [];
};

export const contrastPaper = (value: unknown, choices: readonly PaperColor[]): PaperColor => {
  const used = new Set(pictoColors(value));
  return choices.find((c) => !used.has(c)) ?? choices[0];
};

export const PictoArt: React.FC<{ name: unknown; size: number; style?: React.CSSProperties }> = ({ name, size, style }) => {
  const flag = flagCode(name);
  if (flag) return <FlagArt code={flag} size={size} />;
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
  react?: boolean;
  style?: React.CSSProperties;
};

export const beatPose = (beat: Beat | null): { scale: number; rotate: number; lift: number } => {
  if (!beat) return { scale: 1, rotate: 0, lift: 0 };
  const swing = Math.sin(beat.t * Math.PI * 2) * (1 - beat.t);
  return { scale: 1 + 0.16 * beat.wave, rotate: (beat.index % 2 === 0 ? 9 : -9) * swing, lift: -26 * beat.wave };
};

export const Picto: React.FC<PictoProps> = ({ name, size, x, y, enterAt = SUPPORT_AT, rotate = 0, seed, float = 7, motion, react = true, style }) => {
  const frame = useCurrentFrame();
  const beat = useBeat();
  if (!hasVisual(name)) return null;
  const key = seed ?? `picto-${String(name)}`;
  const e = entry(frame, enterAt, { dy: 40, spin: rotate >= 0 ? 8 : -8, from: 0.9, ...motion });
  const d = drift(key, frame, float, 2.4);
  const placed: React.CSSProperties = x !== undefined || y !== undefined ? { position: "absolute", left: x ?? 0, top: y ?? 0 } : { position: "relative" };
  const pose = beatPose(react ? beat : null);
  return (
    <div style={{ ...placed, width: size, height: size, opacity: e.opacity, transform: paperTransform(e, d, rotate), ...style }}>
      <div style={{ transform: `translateY(${pose.lift}px) rotate(${pose.rotate}deg) scale(${pose.scale})`, transformOrigin: "50% 80%" }}>
        <PictoArt name={name} size={size} />
      </div>
    </div>
  );
};
