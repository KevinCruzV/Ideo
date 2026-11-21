import React from "react";
import { Img } from "remotion";
import grainUrl from "../../public/grain.png";
import { cutEdge } from "../paper/motion";
import { shade } from "../theme";
import { FlagCode } from "./flags";

const files = require.context("flag-icons/flags/4x3", false, /^\.\/[a-z]{2}\.svg$/);

export const flagUrl = (code: FlagCode): string | null => (code === "su" ? null : files(`./${code}.svg`));

const SOVIET_RED = "#cc0000";
const SOVIET_GOLD = "#ffd700";

const starPoints = (cx: number, cy: number, ro: number, ri: number): string =>
  Array.from({ length: 10 }, (_, i) => {
    const r = i % 2 === 0 ? ro : ri;
    const a = (-90 + 36 * i) * (Math.PI / 180);
    return `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`;
  }).join(" ");

export const SovietFlag: React.FC = () => (
  <svg viewBox="0 0 400 300" width="100%" height="100%" preserveAspectRatio="none" style={{ display: "block" }}>
    <rect width="400" height="300" fill={SOVIET_RED} />
    <polygon points={starPoints(75, 34, 16, 6.5)} fill="none" stroke={SOVIET_GOLD} strokeWidth="3.5" strokeLinejoin="round" />
    <path d="M83.4 57.6 A24 24 0 1 1 44.8 82.2 L55.5 78.4 A19 19 0 1 0 88.0 59.3 Z" fill={SOVIET_GOLD} />
    <line x1="42.8" y1="84.2" x2="40" y2="102" stroke={SOVIET_GOLD} strokeWidth="7" />
    <line x1="50" y1="106" x2="88" y2="62" stroke={SOVIET_GOLD} strokeWidth="6.5" />
    <line x1="78" y1="51" x2="98" y2="72" stroke={SOVIET_GOLD} strokeWidth="11" />
  </svg>
);

export const FlagArt: React.FC<{ code: FlagCode; size: number }> = ({ code, size }) => {
  const width = size * 0.94;
  const height = width * 0.75;
  const edge = cutEdge(`flag-${code}`, 0.7);
  const url = flagUrl(code);
  const off = Math.max(2, size * 0.016);
  return (
    <div style={{ position: "relative", width: size, height: size, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ position: "relative", width, height }}>
        <div style={{ position: "absolute", inset: 0, transform: `translate(${off}px, ${off * 1.35}px)`, background: shade, clipPath: edge }} />
        <div style={{ position: "absolute", inset: 0, clipPath: edge, overflow: "hidden", background: "#fff" }}>
          {url ? <Img src={url} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} /> : <SovietFlag />}
          <div
            style={{
              position: "absolute",
              inset: 0,
              backgroundImage: `url(${grainUrl})`,
              backgroundSize: "384px 384px",
              mixBlendMode: "multiply",
              opacity: 0.55,
            }}
          />
        </div>
      </div>
    </div>
  );
};
