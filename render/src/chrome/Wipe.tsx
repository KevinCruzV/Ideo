import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { hash, signed } from "../paper/motion";
import { colors, layout, PaperColor, shade, SHADOW_X, SHADOW_Y } from "../theme";

export const WIPE_BEFORE = 7;
export const WIPE_AFTER = 2;
export const WIPE_FRAMES = WIPE_BEFORE + WIPE_AFTER;
export const WIPE_KINDS = ["slide", "rise", "tear", "blinds", "zoom"] as const;
export type WipeKind = (typeof WIPE_KINDS)[number];

const W = layout.width;
const H = layout.height;
const CX = W / 2;
const CY = H / 2;
const SHEET_W = 1500;
const SHEET_H = 2400;
const TRAVEL = CX + SHEET_W / 2 + 260;
const RISE_W = 1700;
const RISE_H = 2500;
const RISE_TRAVEL = CY + RISE_H / 2 + 260;
const STRIPS = 6;
const STRIP_PITCH = W / STRIPS;
const STRIP_W = STRIP_PITCH + 140;
const STRIP_H = 2200;
const TEAR_REACH = 1400;
const TEAR_SEAM_OVERLAP = 6;
const ZOOM_RADIUS = 1350;

const easeIn = (t: number) => t * t;
const easeOut = (t: number) => 1 - (1 - t) * (1 - t);
const clamp01 = (t: number) => Math.min(1, Math.max(0, t));

const coverOf = (frame: number) => easeIn(clamp01(frame / WIPE_BEFORE));
const exitOf = (frame: number) => easeOut(clamp01((frame - WIPE_BEFORE) / (WIPE_FRAMES - WIPE_BEFORE)));
const travelOf = (frame: number): number => (frame <= WIPE_BEFORE ? 1 - coverOf(frame) : -exitOf(frame));

export const wipeOffset = (frame: number): number => TRAVEL * travelOf(frame);

export type Pt = [number, number];
export type WipePiece = { pts: Pt[]; tone: "main" | "cream" };

const rectPoly = (cx: number, cy: number, w: number, h: number, deg: number): Pt[] => {
  const r = (deg * Math.PI) / 180;
  const cos = Math.cos(r);
  const sin = Math.sin(r);
  return ([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]] as Pt[]).map(([x, y]) => [cx + x * cos - y * sin, cy + x * sin + y * cos]);
};

const discPoly = (cx: number, cy: number, radius: number): Pt[] =>
  Array.from({ length: 56 }, (_, i) => {
    const a = (i / 56) * Math.PI * 2;
    return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
  });

const tearPieces = (frame: number): WipePiece[] => {
  const away = frame <= WIPE_BEFORE ? 1 - coverOf(frame) : exitOf(frame);
  const lift = away * TEAR_REACH;
  const teeth = Array.from({ length: 15 }, (_, j): Pt => [-60 + 90 * j, CY + (j % 2 === 0 ? -34 : 34)]);
  const top: Pt[] = [[-60, CY - TEAR_REACH - lift], [1200, CY - TEAR_REACH - lift], ...teeth.slice().reverse().map(([x, y]): Pt => [x, y - lift])];
  const bottom: Pt[] = [...teeth.map(([x, y]): Pt => [x, y - TEAR_SEAM_OVERLAP + lift]), [1200, CY + TEAR_REACH + lift], [-60, CY + TEAR_REACH + lift]];
  return [{ pts: top, tone: "main" }, { pts: bottom, tone: "main" }];
};

const blindPieces = (frame: number): WipePiece[] =>
  Array.from({ length: STRIPS }, (_, i) => {
    const down = clamp01((frame / WIPE_BEFORE - i * 0.07) / 0.65);
    const gone = clamp01((frame - WIPE_BEFORE - i * 0.15) / 1.25);
    const y = frame <= WIPE_BEFORE ? -(1 - easeIn(down)) * (STRIP_H + 200) : easeOut(gone) * (STRIP_H + 200);
    const tilt = i % 2 === 0 ? 1.4 : -1.4;
    return { pts: rectPoly(STRIP_PITCH * (i + 0.5), CY + y, STRIP_W, STRIP_H, tilt), tone: i % 2 === 0 ? "main" : "cream" };
  });

export const wipePieces = (kind: WipeKind, frame: number): WipePiece[] => {
  const pos = travelOf(frame);
  switch (kind) {
    case "rise":
      return [{ pts: rectPoly(CX, CY + RISE_TRAVEL * pos, RISE_W, RISE_H, 5), tone: "main" }];
    case "tear":
      return tearPieces(frame);
    case "blinds":
      return blindPieces(frame);
    case "zoom": {
      const radius = frame <= WIPE_BEFORE ? ZOOM_RADIUS * coverOf(frame) : ZOOM_RADIUS * (1 - exitOf(frame));
      return radius < 2 ? [] : [{ pts: discPoly(CX, CY, radius), tone: "main" }];
    }
    case "slide":
    default:
      return [{ pts: rectPoly(CX + TRAVEL * pos, CY, SHEET_W, SHEET_H, -9), tone: "main" }];
  }
};

export const wipeKind = (index: number): WipeKind => {
  let previous = -1;
  let chosen = 0;
  for (let i = 0; i <= Math.max(0, index); i++) {
    const options = WIPE_KINDS.map((_, k) => k).filter((k) => k !== previous);
    chosen = options[Math.floor(hash(`wipe-kind:${i}`) * options.length)];
    previous = chosen;
  }
  return WIPE_KINDS[chosen];
};

export const inside = (pts: Pt[], x: number, y: number): boolean => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i];
    const [xj, yj] = pts[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};

const cutPath = (pts: Pt[], seed: string): string => {
  const out: Pt[] = [];
  pts.forEach(([x, y], i) => {
    const [nx, ny] = pts[(i + 1) % pts.length];
    const length = Math.hypot(nx - x, ny - y);
    const steps = Math.max(1, Math.min(8, Math.round(length / 220)));
    for (let s = 0; s < steps; s++) {
      const t = s / steps;
      out.push([x + (nx - x) * t + signed(`${seed}:${i}:${s}x`, 1.6), y + (ny - y) * t + signed(`${seed}:${i}:${s}y`, 1.6)]);
    }
  });
  return `M${out.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L")} Z`;
};

export const Wipe: React.FC<{ color: PaperColor; seed: string; kind?: WipeKind }> = ({ color, seed, kind = "slide" }) => {
  const frame = useCurrentFrame();
  const pieces = wipePieces(kind, frame);
  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
      {pieces.map((piece, i) => {
        const d = cutPath(piece.pts, `${seed}:${i}`);
        return (
          <g key={i}>
            <path d={d} fill={shade} transform={`translate(${SHADOW_X} ${SHADOW_Y})`} />
            <path d={d} fill={piece.tone === "cream" ? colors.cream : colors[color]} />
          </g>
        );
      })}
    </svg>
  );
};
