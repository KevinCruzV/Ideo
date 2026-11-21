import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, PaperColor } from "../theme";
import { breath, gaze, idleTilt, isBlinking, Mouth, Pose, POSE_SPECS } from "./pose";

const SHADE = "rgba(0,0,0,.22)";

export const VIEW = { x: -92, y: -72, w: 184, h: 176 } as const;
export const HEAD_CENTER = { x: 0, y: -31, r: 33 } as const;
const HEAD_VIEW = { x: -37, y: -68, w: 76, h: 76 } as const;
export const CUT_Y = 36;
const SHOULDERS = "M-36 -6 L37 -7 Q51 -5 55 8 L68 104 L-66 104 L-53 8 Q-49 -4 -36 -6 Z";

const shadeOffset = (px: number, unitsPerPx: number): [number, number] => {
  const dx = Math.max(2, px * 0.008);
  return [dx * unitsPerPx, dx * 1.5 * unitsPerPx];
};

const MouthShape: React.FC<{ mouth: Mouth }> = ({ mouth }) => {
  if (mouth === "open") return <ellipse cx={1} cy={-16} rx={5.2} ry={6.6} fill={colors.ink} />;
  if (mouth === "flat")
    return <path d="M-5 -17.5 L6 -18.5" fill="none" stroke={colors.ink} strokeWidth={4.5} strokeLinecap="round" />;
  return <path d="M-9 -19 Q1 -9 12 -19" fill="none" stroke={colors.ink} strokeWidth={4.5} strokeLinecap="round" />;
};

type FaceProps = { pose: Pose; blink: boolean; tilt: number; shade: [number, number]; look?: [number, number] };

const Face: React.FC<FaceProps> = ({ pose, blink, tilt, shade, look = [0, 0] }) => {
  const spec = POSE_SPECS[pose];
  const eyes: [number, number][] = [
    [-11, -35],
    [12, -35],
  ];
  return (
    <g transform={`rotate(${tilt} 0 -30)`}>
      <circle cx={HEAD_CENTER.x + shade[0]} cy={HEAD_CENTER.y + shade[1]} r={HEAD_CENTER.r} fill={SHADE} />
      <circle cx={HEAD_CENTER.x} cy={HEAD_CENTER.y} r={HEAD_CENTER.r} fill={colors.yellow} />
      {eyes.map(([cx, cy], i) =>
        blink ? (
          <path
            key={`eye-${i}`}
            d={`M${cx - spec.eyeR * 0.85} ${cy + 1} L${cx + spec.eyeR * 0.85} ${cy + 1}`}
            fill="none"
            stroke={colors.ink}
            strokeWidth={3.4}
            strokeLinecap="round"
          />
        ) : (
          <g key={`eye-${i}`}>
            <circle cx={cx} cy={cy} r={spec.eyeR} fill={colors.cream} />
            <circle cx={cx + spec.look[0] + look[0]} cy={cy + spec.look[1] + look[1]} r={spec.pupilR} fill={colors.ink} />
          </g>
        ),
      )}
      <MouthShape mouth={spec.mouth} />
    </g>
  );
};

const ARM = "M0 -5.5 L28 -5.5 L28 -11.5 L46 0 L28 11.5 L28 5.5 L0 5.5 Z";

export type CharacterProps = {
  size: number;
  pose?: Pose;
  body?: PaperColor;
  seed?: string;
  lift?: number;
  style?: React.CSSProperties;
};

export const characterWidth = (size: number): number => (size * VIEW.w) / VIEW.h;

export const sizeForHead = (headPx: number): number => (headPx * VIEW.h) / (HEAD_CENTER.r * 2);

export const Character: React.FC<CharacterProps> = ({
  size,
  pose = "question",
  body = "blue",
  seed = "mascot",
  lift = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const spec = POSE_SPECS[pose];
  const shade = shadeOffset(size, VIEW.h / size);
  const tilt = spec.headTilt + idleTilt(seed, frame);
  const blink = isBlinking(seed, frame);
  const fill = colors[body];
  const look = gaze(seed, frame);
  const chest = breath(frame);

  return (
    <svg
      width={characterWidth(size)}
      height={size}
      viewBox={`${VIEW.x} ${VIEW.y} ${VIEW.w} ${VIEW.h}`}
      style={{ position: "absolute", overflow: "visible", transform: `translateY(${-lift * size}px)`, ...style }}
    >
      <g transform={`rotate(${spec.lean} 0 ${CUT_Y})`}>
        <g transform={`rotate(3 0 40) translate(0 ${CUT_Y + 68}) scale(${2 - chest} ${chest}) translate(0 ${-(CUT_Y + 68)})`}>
          <path d={SHOULDERS} fill={SHADE} transform={`translate(${shade[0]} ${shade[1]})`} />
          <path d={SHOULDERS} fill={fill} />
        </g>
        {spec.arm ? (
          <g transform="translate(44 10) rotate(-34)">
            <path d={ARM} fill={SHADE} transform={`translate(${shade[0]} ${shade[1]})`} />
            <path d={ARM} fill={fill} />
          </g>
        ) : null}
        <g transform={`translate(0 ${(1 - chest) * 60})`}>
          <Face pose={pose} blink={blink} tilt={tilt} shade={shade} look={look} />
        </g>
      </g>
    </svg>
  );
};

export const MascotHead: React.FC<{ size: number; style?: React.CSSProperties }> = ({ size, style }) => {
  const shade = shadeOffset(size, HEAD_VIEW.h / size);
  return (
    <svg
      width={size}
      height={size}
      viewBox={`${HEAD_VIEW.x} ${HEAD_VIEW.y} ${HEAD_VIEW.w} ${HEAD_VIEW.h}`}
      style={{ display: "block", overflow: "visible", ...style }}
    >
      <Face pose="content" blink={false} tilt={-6} shade={shade} />
    </svg>
  );
};
