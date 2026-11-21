import React from "react";
import { colors, shade } from "../theme";
import { BodyPose, BodySetting } from "./bodyOptions";
import { P, Rig } from "./bodyRig";

const ARM = 15;
const LEG = 19;
const OFF: P = [2.2, 3];

const Seg: React.FC<{ a: P; b: P; w: number; color: string }> = ({ a, b, w, color }) => (
  <>
    <line x1={a[0] + OFF[0]} y1={a[1] + OFF[1]} x2={b[0] + OFF[0]} y2={b[1] + OFF[1]} stroke={shade} strokeWidth={w} strokeLinecap="round" />
    <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color} strokeWidth={w} strokeLinecap="round" />
  </>
);

const Blob: React.FC<{ d: string; fill: string }> = ({ d, fill }) => (
  <>
    <path d={d} fill={shade} transform={`translate(${OFF[0]} ${OFF[1]})`} />
    <path d={d} fill={fill} />
  </>
);

const mid = (a: P, b: P): P => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];

const torsoPath = (rig: Rig): string => {
  const top = mid(rig.shoulders[0], rig.shoulders[1]);
  const bottom = mid(rig.hips[0], rig.hips[1]);
  const dx = bottom[0] - top[0];
  const dy = bottom[1] - top[1];
  const len = Math.hypot(dx, dy) || 1;
  const nx = -dy / len;
  const ny = dx / len;
  const [wt, wb] = rig.torso;
  const t1: P = [top[0] + nx * (wt / 2) - (dx / len) * 6, top[1] + ny * (wt / 2) - (dy / len) * 6];
  const t2: P = [top[0] - nx * (wt / 2) - (dx / len) * 6, top[1] - ny * (wt / 2) - (dy / len) * 6];
  const b1: P = [bottom[0] + nx * (wb / 2) + (dx / len) * 6, bottom[1] + ny * (wb / 2) + (dy / len) * 6];
  const b2: P = [bottom[0] - nx * (wb / 2) + (dx / len) * 6, bottom[1] - ny * (wb / 2) + (dy / len) * 6];
  const r = 9;
  return `M${t1[0]} ${t1[1]} Q${top[0] - (dx / len) * (6 + r)} ${top[1] - (dy / len) * (6 + r)} ${t2[0]} ${t2[1]} L${b2[0]} ${b2[1]} L${b1[0]} ${b1[1]} Z`;
};

const shoe = (knee: P, foot: P, rig: Rig, side: number): React.ReactNode => {
  const facing = rig.headView === "right" ? 1 : rig.headView === "left" ? -1 : 0;
  if (rig.feetUp) {
    return <ellipse cx={foot[0]} cy={foot[1] + 4} rx={9} ry={12} fill={colors.red} />;
  }
  const angle = (Math.atan2(foot[1] - knee[1], foot[0] - knee[0]) * 180) / Math.PI;
  const forward = facing !== 0 ? facing : side;
  return (
    <g transform={`translate(${foot[0]} ${foot[1]}) rotate(${angle - 90})`}>
      <ellipse cx={forward * 7 * (facing !== 0 ? 1 : 0.4)} cy={4} rx={rig.topView && facing === 0 ? 9 : 14} ry={8} fill={shade} transform="translate(2 3)" />
      <ellipse cx={forward * 7 * (facing !== 0 ? 1 : 0.4)} cy={4} rx={rig.topView && facing === 0 ? 9 : 14} ry={8} fill={colors.red} />
    </g>
  );
};

const Eye: React.FC<{ x: number; y: number; closed: boolean; look: number; scale?: number }> = ({ x, y, closed, look, scale = 1 }) =>
  closed ? (
    <path d={`M${x - 6 * scale} ${y} Q${x} ${y + 4 * scale} ${x + 6 * scale} ${y}`} fill="none" stroke={colors.ink} strokeWidth={3} strokeLinecap="round" />
  ) : (
    <g>
      <circle cx={x} cy={y} r={6.5 * scale} fill={colors.cream} />
      <circle cx={x + look} cy={y} r={3 * scale} fill={colors.ink} />
    </g>
  );

export const Head: React.FC<{ rig: Rig; blink: boolean; tilt: number; look: number }> = ({ rig, blink, tilt, look }) => {
  const [hx, hy] = rig.head;
  const closed = rig.asleep || blink;
  const r = 27;
  const view = rig.headView;
  return (
    <g transform={`rotate(${tilt} ${hx} ${hy + 10})`}>
      <circle cx={hx + OFF[0]} cy={hy + OFF[1]} r={r} fill={shade} />
      <circle cx={hx} cy={hy} r={r} fill={colors.yellow} />
      {view === "front" ? (
        <>
          <Eye x={hx - 10} y={hy - 3} closed={closed} look={look} />
          <Eye x={hx + 10} y={hy - 3} closed={closed} look={look} />
          <path d={`M${hx - 6} ${hy + 11} Q${hx} ${hy + (rig.asleep ? 13 : 16)} ${hx + 6} ${hy + 11}`} fill="none" stroke={colors.ink} strokeWidth={3} strokeLinecap="round" />
        </>
      ) : view === "back" ? (
        <>
          <Eye x={hx + 18} y={hy - 2} closed look={0} scale={0.7} />
          <path d={`M${hx - 14} ${hy + 18} Q${hx} ${hy + 24} ${hx + 14} ${hy + 18}`} fill="none" stroke="rgba(31,26,20,.25)" strokeWidth={3} strokeLinecap="round" />
        </>
      ) : (
        (() => {
          const f = view === "right" ? 1 : -1;
          return (
            <>
              <Eye x={hx + f * 4} y={hy - 4} closed={closed} look={f * 2 + look} />
              <Eye x={hx + f * 18} y={hy - 4} closed={closed} look={f * 2 + look} scale={0.8} />
              <path d={`M${hx + f * 6} ${hy + 12} L${hx + f * 17} ${hy + 11}`} fill="none" stroke={colors.ink} strokeWidth={3} strokeLinecap="round" />
            </>
          );
        })()
      )}
    </g>
  );
};

export const BodyFigure: React.FC<{ rig: Rig; blink: boolean; tilt: number; look: number }> = ({ rig, blink, tilt, look }) => {
  const near = rig.headView === "left" ? 0 : 1;
  const far = 1 - near;
  const profile = rig.headView === "right" || rig.headView === "left";
  const order = profile ? [far, near] : [0, 1];
  const legs = order.map((i) => (
    <g key={`leg-${i}`}>
      <Seg a={rig.hips[i]} b={rig.knees[i]} w={LEG} color={profile && i === far ? "#3b352d" : colors.ink} />
      <Seg a={rig.knees[i]} b={rig.feet[i]} w={LEG - 2} color={profile && i === far ? "#3b352d" : colors.ink} />
      {shoe(rig.knees[i], rig.feet[i], rig, i === 0 ? -1 : 1)}
    </g>
  ));
  const arm = (i: number) => (
    <g key={`arm-${i}`}>
      <Seg a={rig.shoulders[i]} b={rig.elbows[i]} w={ARM} color={profile && i === far ? "#1d3aa6" : colors.blue} />
      <Seg a={rig.elbows[i]} b={rig.hands[i]} w={ARM - 1} color={profile && i === far ? "#1d3aa6" : colors.blue} />
      <circle cx={rig.hands[i][0] + OFF[0]} cy={rig.hands[i][1] + OFF[1]} r={8.5} fill={shade} />
      <circle cx={rig.hands[i][0]} cy={rig.hands[i][1]} r={8.5} fill={colors.yellow} />
    </g>
  );
  return (
    <g>
      {profile ? arm(far) : null}
      {legs}
      <Blob d={torsoPath(rig)} fill={colors.blue} />
      {profile ? arm(near) : [arm(0), arm(1)]}
      <Head rig={rig} blink={blink} tilt={tilt} look={look} />
    </g>
  );
};

const KRAFT = "#ddd0b4";

export const SettingBack: React.FC<{ setting: BodySetting; pose: BodyPose; rig: Rig }> = ({ setting, pose, rig }) => {
  const lying = pose.startsWith("lying");
  if (setting === "bed") {
    if (lying) {
      return (
        <g>
          <rect x={112 + OFF[0]} y={14 + OFF[1]} width={176} height={296} rx={12} fill={shade} />
          <rect x={112} y={14} width={176} height={296} rx={12} fill={colors.red} />
          <rect x={122} y={24} width={156} height={278} rx={8} fill={colors.cream} />
          <rect x={146 + OFF[0]} y={30 + OFF[1]} width={108} height={52} rx={18} fill={shade} />
          <rect x={146} y={30} width={108} height={52} rx={18} fill="#f3ead6" />
          <rect x={122} y={276} width={156} height={26} fill={colors.blue} />
          <rect x={122} y={276} width={156} height={6} fill="rgba(31,26,20,.18)" />
        </g>
      );
    }
    return (
      <g>
        <rect x={60} y={190} width={280} height={60} rx={8} fill={colors.red} />
        <rect x={66} y={176} width={268} height={26} rx={6} fill={colors.cream} />
        <rect x={60} y={150} width={18} height={110} fill={colors.red} />
      </g>
    );
  }
  if (setting === "chair" || setting === "desk") {
    const seatY = rig.hips[0][1] + 10;
    const seatX = rig.hips[0][0] - 26;
    return (
      <g>
        <rect x={seatX - 4} y={seatY - 76} width={10} height={86} rx={3} fill={colors.red} />
        <rect x={seatX - 4} y={seatY} width={58} height={10} rx={3} fill={colors.red} />
        <rect x={seatX} y={seatY + 10} width={7} height={62} fill={colors.red} />
        <rect x={seatX + 44} y={seatY + 10} width={7} height={62} fill={colors.red} />
      </g>
    );
  }
  if (setting === "outdoor") {
    return (
      <g>
        <circle cx={330} cy={60} r={26} fill={colors.yellow} />
        <rect x={30} y={272} width={340} height={18} rx={4} fill={KRAFT} />
        {[70, 120, 290, 340].map((x) => (
          <path key={x} d={`M${x} 272 L${x + 5} 258 L${x + 9} 272 L${x + 14} 262 L${x + 17} 272 Z`} fill="#3b352d" />
        ))}
      </g>
    );
  }
  if (!lying) {
    return <ellipse cx={(rig.feet[0][0] + rig.feet[1][0]) / 2} cy={Math.max(rig.feet[0][1], rig.feet[1][1]) + 12} rx={58} ry={9} fill="rgba(31,26,20,.14)" />;
  }
  return null;
};

export const SettingFront: React.FC<{ setting: BodySetting; rig: Rig }> = ({ setting, rig }) => {
  if (setting !== "desk") return null;
  const top = rig.hands[0][1] + 6;
  return (
    <g>
      <rect x={216 + OFF[0]} y={top + OFF[1]} width={150} height={12} rx={3} fill={shade} />
      <rect x={216} y={top} width={150} height={12} rx={3} fill="#a46a45" />
      <rect x={228} y={top + 12} width={9} height={270 - top} fill="#8a5636" />
      <rect x={348} y={top + 12} width={9} height={270 - top} fill="#8a5636" />
      <rect x={300} y={top - 46} width={44} height={46} rx={3} fill={colors.ink} />
      <rect x={304} y={top - 42} width={36} height={32} fill={colors.blue} />
    </g>
  );
};
