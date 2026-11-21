import React from "react";
import { useCurrentFrame } from "remotion";
import { Cutter } from "../pictos/cut";
import { breath, isBlinking } from "../mascot/pose";
import { colors, fonts, shade } from "../theme";

const cutter = new Cutter("person-bust", 0.5);
const JACKET = cutter.path([
  [18, 128],
  [24, 96],
  [40, 84],
  [62, 78],
  [100, 76],
  [138, 78],
  [160, 84],
  [176, 96],
  [182, 128],
]);
const SHIRT = cutter.path([
  [80, 78],
  [120, 78],
  [100, 112],
]);
const LAPEL_L = cutter.path([
  [80, 78],
  [100, 112],
  [88, 126],
  [70, 82],
]);
const LAPEL_R = cutter.path([
  [120, 78],
  [130, 82],
  [112, 126],
  [100, 112],
]);
const NECK = cutter.path([
  [88, 60],
  [112, 60],
  [114, 82],
  [86, 82],
]);
const HAIR = cutter.path([
  [64, 40],
  [66, 22],
  [80, 10],
  [100, 6],
  [120, 10],
  [134, 22],
  [136, 40],
  [128, 30],
  [110, 26],
  [86, 28],
  [72, 34],
]);
const head = (cx: number, cy: number, r: number) =>
  cutter.path(Array.from({ length: 26 }, (_, i) => [cx + r * Math.cos((i / 26) * Math.PI * 2), cy + r * 1.08 * Math.sin((i / 26) * Math.PI * 2)] as [number, number]), 0.3);
const HEAD = head(100, 40, 34);

const Layer: React.FC<{ d: string; fill: string }> = ({ d, fill }) => (
  <>
    <path d={d} fill={shade} transform="translate(1.6 2.2)" />
    <path d={d} fill={fill} />
  </>
);

export const PersonBust: React.FC<{ width: number; initials: string; badge: string; badgeInk: string }> = ({ width, initials, badge, badgeInk }) => {
  const frame = useCurrentFrame();
  const chest = breath(frame + 11);
  const blink = isBlinking("person", frame);
  const tilt = 1.6 * Math.sin((frame / 30) * 0.8);
  return (
    <svg width={width} height={(width * 128) / 200} viewBox="0 0 200 128" style={{ display: "block", overflow: "visible" }}>
      <g transform={`translate(0 128) scale(1 ${chest}) translate(0 -128)`}>
        <Layer d={JACKET} fill={colors.ink} />
        <Layer d={SHIRT} fill={colors.cream} />
        <Layer d={LAPEL_L} fill={colors.ink} />
        <Layer d={LAPEL_R} fill={colors.ink} />
        <g transform="translate(140 100) rotate(-6)">
          <circle cx={1.6} cy={2.2} r={17} fill={shade} />
          <circle r={17} fill={badge} />
          <text
            textAnchor="middle"
            dominantBaseline="central"
            fontFamily={fonts.text}
            fontWeight={800}
            fontSize={initials.length > 1 ? 15 : 19}
            fill={badgeInk}
            letterSpacing={-0.5}
          >
            {initials}
          </text>
        </g>
      </g>
      <g transform={`translate(0 ${(1 - chest) * 40}) rotate(${tilt} 100 70)`}>
        <Layer d={NECK} fill={colors.cream} />
        <Layer d={HEAD} fill={colors.cream} />
        <Layer d={HAIR} fill={colors.ink} />
        {blink ? (
          <>
            <rect x={84} y={44} width={9} height={2.2} fill={colors.ink} />
            <rect x={107} y={44} width={9} height={2.2} fill={colors.ink} />
          </>
        ) : (
          <>
            <circle cx={88.5} cy={45} r={3.3} fill={colors.ink} />
            <circle cx={111.5} cy={45} r={3.3} fill={colors.ink} />
          </>
        )}
        <rect x={93} y={58} width={14} height={2.6} fill={colors.ink} transform="rotate(-2 100 59)" />
      </g>
    </svg>
  );
};
