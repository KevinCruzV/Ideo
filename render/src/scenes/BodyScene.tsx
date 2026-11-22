import React from "react";
import { useCurrentFrame } from "remotion";
import { isBlinking } from "../mascot/pose";
import { entry, tween } from "../paper/motion";
import { stripHeight } from "../paper/PaperStrip";
import { Strips } from "./Strips";
import { colors } from "../theme";
import { fitText, textWidth } from "../text/fit";
import { useBeat } from "./beats";
import { BodyFigure, SettingBack, SettingFront } from "./BodyFigure";
import { BodyPart, bodyPart, bodyPose, bodySetting, BodyTone, bodyTone } from "./bodyOptions";
import { Anchor, anchorOf, P, rigOf } from "./bodyRig";
import { list, str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { enterFor } from "./timing";

const UPRIGHT_VIEW = [56, 0, 288, 320] as const;
const LYING_VIEW = [46, 64, 312, 192] as const;

export const rotateLying = ([x, y]: P): P => [200 + (y - 160), 160 - (x - 200)];
const LABEL_MAX = 52;
const LABEL_MIN = 44;

export const toneColor = (tone: BodyTone): string => ({ good: colors.blue, bad: colors.red, neutral: colors.yellow })[tone];

type Mark = { part: BodyPart; label: string };

export const marksOf = (value: unknown): Mark[] =>
  list(value, 4).flatMap((m) => {
    const o = m && typeof m === "object" ? (m as Record<string, unknown>) : { part: m };
    const part = bodyPart(o.part);
    return part ? [{ part, label: str(o.label).slice(0, 28) }] : [];
  });

const Organ: React.FC<{ part: BodyPart; a: Anchor; color: string; spine: [P, P] }> = ({ part, a, color, spine }) => {
  const [x, y] = a.at;
  const edge = { stroke: colors.cream, strokeWidth: 2.4, fill: color };
  if (part === "heart") {
    const s = 0.55;
    return (
      <path
        d={`M${x} ${y + 12 * s} C${x - 22 * s} ${y - 2 * s} ${x - 14 * s} ${y - 22 * s} ${x} ${y - 10 * s} C${x + 14 * s} ${y - 22 * s} ${x + 22 * s} ${y - 2 * s} ${x} ${y + 12 * s} Z`}
        {...edge}
      />
    );
  }
  if (part === "lungs") {
    return (
      <g {...edge}>
        <ellipse cx={x - 10} cy={y + 2} rx={8.5} ry={15} />
        <ellipse cx={x + 10} cy={y + 2} rx={8.5} ry={15} />
      </g>
    );
  }
  if (part === "stomach") {
    return <path d={`M${x - 10} ${y - 8} Q${x + 14} ${y - 14} ${x + 10} ${y + 4} Q${x + 4} ${y + 14} ${x - 8} ${y + 8} Q${x - 2} ${y} ${x - 10} ${y - 8} Z`} {...edge} />;
  }
  if (part === "brain") {
    return (
      <g {...edge}>
        {[
          [-9, -2],
          [0, -7],
          [9, -2],
          [-4, 5],
          [5, 5],
        ].map(([dx, dy], i) => (
          <circle key={i} cx={x + dx} cy={y + dy} r={7} />
        ))}
      </g>
    );
  }
  if (part === "spine") {
    const [top, bottom] = spine;
    return (
      <g {...edge}>
        {Array.from({ length: 6 }, (_, i) => {
          const t = (i + 0.5) / 6;
          return <rect key={i} x={top[0] + (bottom[0] - top[0]) * t - 5} y={top[1] + (bottom[1] - top[1]) * t - 4} width={10} height={8} rx={2} />;
        })}
      </g>
    );
  }
  return null;
};

export const BodyScene: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const beat = useBeat(14);
  const pose = bodyPose(props.pose);
  const setting = bodySetting(props.setting);
  const tone = bodyTone(props.tone);
  const color = toneColor(tone);
  const rig = rigOf(pose);
  const marks = marksOf(props.marks);
  const top = areaTop(props);
  const area = areaFor(top + 10, BOX_L, BOX_W);
  const lying = pose.startsWith("lying");
  const breath = Math.sin((frame / 30) * Math.PI * 2 * (lying ? 0.22 : 0.3));
  const nod = beat ? 6 * Math.sin(beat.t * Math.PI * 2) * (1 - beat.t) : 0;
  const tilt = (lying ? 2.5 * Math.sin((frame / 30) * 0.5) : 1.5 * Math.sin((frame / 30) * 0.9)) + nod;
  const look = beat ? (beat.index % 2 ? -2 : 2) * beat.wave : 1.2 * Math.sin((frame / 30) * 0.6);
  const blink = !lying && isBlinking("body", frame);
  const pelvis: P = [(rig.hips[0][0] + rig.hips[1][0]) / 2, (rig.hips[0][1] + rig.hips[1][1]) / 2];
  const neck: P = [(rig.shoulders[0][0] + rig.shoulders[1][0]) / 2, (rig.shoulders[0][1] + rig.shoulders[1][1]) / 2];
  const figure = entry(frame, -3, { dy: 30, spin: 0, from: 0.95 });

  const W = BOX_W;
  const view = lying ? LYING_VIEW : UPRIGHT_VIEW;
  const [VX, VY, VW, VH] = view;
  const s = W / VW;
  const H = VH * s;
  const toView = (pt: P): P => (lying ? rotateLying(pt) : pt);
  const labelW = lying ? W * 0.48 : W * 0.46;
  const maxLines = lying ? 2 : 3;
  const labelFits = marks.map((m) => fitText(m.label, { maxWidth: labelW, maxLines, max: LABEL_MAX, min: LABEL_MIN, prefer: true }));
  const labelSize = Math.max(LABEL_MIN, Math.min(LABEL_MAX, ...labelFits.filter((f) => f.lines.length).map((f) => f.size)));
  const fits = marks.map((m) => fitText(m.label, { maxWidth: labelW, maxLines, max: labelSize, min: LABEL_MIN, prefer: true }));
  const lineH = stripHeight(labelSize);
  const base = marks.map((m, i) => {
    const a = anchorOf(rig, m.part);
    const [vx, vy] = toView(a.at);
    const fit = fits[i];
    const labelH = fit.lines.length * lineH + Math.max(0, fit.lines.length - 1) * 6;
    const w = fit.lines.length ? Math.max(...fit.lines.map((l) => textWidth(l, fit.size) + fit.size * 0.6)) : 0;
    return { ...m, a, ax: (vx - VX) * s, ay: (vy - VY) * s, fit, labelH, w, at: enterFor(`marks.${i}`, items, from, to) };
  });
  type Placed = (typeof base)[number] & { left: number; y: number; side: number };
  let placed: Placed[] = [];
  let svgTop = 0;
  let totalH = H;
  if (lying) {
    const rows: Placed[][] = [[], []];
    base.forEach((m) => {
      let row = m.ay < H / 2 ? 0 : 1;
      if (rows[row].length >= 2 && rows[1 - row].length < 2) row = 1 - row;
      rows[row].push({ ...m, left: 0, y: 0, side: row === 0 ? -1 : 1 });
    });
    const packRow = (row: Placed[]) => {
      const sorted = [...row].sort((p, q) => p.ax - q.ax);
      let line = 0;
      let cursor = 0;
      const lines: number[] = [];
      sorted.forEach((m) => {
        let left = Math.max(0, Math.min(W - m.w, m.ax - m.w / 2));
        if (left < cursor) left = cursor;
        if (left + m.w > W) {
          line += 1;
          left = Math.max(0, Math.min(W - m.w, m.ax - m.w / 2));
        }
        m.left = left;
        m.y = line;
        cursor = left + m.w + 18;
        lines[line] = Math.max(lines[line] ?? 0, m.labelH);
      });
      return lines;
    };
    const topLines = packRow(rows[0]);
    const bottomLines = packRow(rows[1]);
    const topH = topLines.reduce((sum, h) => sum + h + 14, 0);
    svgTop = topH ? topH + 20 : 0;
    rows[0].forEach((m) => {
      m.y = topLines.slice(0, m.y).reduce((sum, h) => sum + h + 14, 0);
    });
    rows[1].forEach((m) => {
      m.y = svgTop + H + 20 + bottomLines.slice(0, m.y).reduce((sum, h) => sum + h + 14, 0);
    });
    const bottomH = bottomLines.reduce((sum, h) => sum + h + 14, 0);
    totalH = svgTop + H + (bottomH ? bottomH + 20 : 0);
    placed = [...rows[0], ...rows[1]];
  } else {
    const slots: { side: number; y: number; h: number }[] = [];
    placed = base.map((m) => {
      let side = m.ax < W / 2 ? -1 : 1;
      if (slots.filter((sl) => sl.side === side).length >= 2 && slots.filter((sl) => sl.side === -side).length < 2) side = -side;
      let y = m.ay - m.labelH / 2;
      for (const sl of slots.filter((sl) => sl.side === side).sort((p, q) => p.y - q.y)) {
        if (y < sl.y + sl.h + 14 && y + m.labelH > sl.y - 14) y = sl.y + sl.h + 14;
      }
      y = Math.max(-m.labelH * 0.2, Math.min(H - m.labelH, y));
      slots.push({ side, y, h: m.labelH });
      return { ...m, side, y, left: side < 0 ? 0 : W - m.w };
    });
  }
  const layout = placed.map((m) => ({ ...m, px: m.ax, py: m.ay + svgTop }));
  const groupTransform = lying ? `rotate(-90 200 160)` : undefined;

  return (
    <Stage>
      <FitBox area={area}>
        <div style={{ position: "relative", width: W, height: totalH }}>
          <svg
            width={W}
            height={H}
            viewBox={`${VX} ${VY} ${VW} ${VH}`}
            style={{ position: "absolute", left: 0, top: svgTop, overflow: "visible", opacity: figure.opacity, transform: `translateY(${figure.y}px)` }}
          >
            <g transform={groupTransform}>
            <SettingBack setting={setting} pose={pose} rig={rig} />
            {layout.map((m) => {
              const on = tween(frame, m.at, 10);
              const pulse = beat && beat.index % Math.max(1, layout.length) === layout.indexOf(m) ? beat.wave : 0;
              return (
                <ellipse
                  key={`halo-${m.part}`}
                  cx={m.a.at[0]}
                  cy={m.a.at[1]}
                  rx={(m.a.rx + 8) * (0.9 + 0.1 * on) * (1 + 0.12 * pulse)}
                  ry={(m.a.ry + 8) * (0.9 + 0.1 * on) * (1 + 0.12 * pulse)}
                  fill={color}
                  opacity={0.3 * on}
                />
              );
            })}
            <g transform={`translate(${pelvis[0]} ${pelvis[1]}) scale(${1 + 0.008 * breath} ${1 + 0.014 * breath}) translate(${-pelvis[0]} ${-pelvis[1]})`}>
              <BodyFigure rig={rig} blink={blink} tilt={tilt} look={look} />
            </g>
            <SettingFront setting={setting} rig={rig} />
            {layout.map((m) => {
              const on = tween(frame, m.at, 10);
              return (
                <g key={`mark-${m.part}`} opacity={on}>
                  <ellipse cx={m.a.at[0]} cy={m.a.at[1]} rx={m.a.rx + 6} ry={m.a.ry + 6} fill="none" stroke={color} strokeWidth={4.5} strokeDasharray="10 6" />
                  <g opacity={0.92}>
                    <Organ part={m.part} a={m.a} color={color} spine={[neck, pelvis]} />
                  </g>
                </g>
              );
            })}
            </g>
          </svg>
          {layout.map((m) => {
            if (!m.label) return null;
            const on = tween(frame, m.at + 2, 8);
            const lx = lying ? m.left + m.w / 2 : m.side < 0 ? m.left + m.w - 6 : m.left + 6;
            const ly = lying ? (m.side < 0 ? m.y + m.labelH - 8 : m.y + 8) : m.y + Math.min(m.labelH, lineH) / 2;
            const tx = m.px;
            return (
              <React.Fragment key={`label-${m.part}`}>
                <svg width={W} height={totalH} style={{ position: "absolute", left: 0, top: 0, overflow: "visible", opacity: on }}>
                  <line x1={lx} y1={ly} x2={lx + (tx - lx) * on} y2={ly + (m.py - ly) * on} stroke={colors.ink} strokeWidth={4} strokeLinecap="round" />
                  <circle cx={m.px} cy={m.py} r={7 * on} fill={colors.ink} />
                </svg>
                <div style={{ position: "absolute", left: m.left, top: m.y }}>
                  <Strips lines={m.fit.lines} size={m.fit.size} enterAt={m.at + 2} seed={`body-label-${m.part}`} gap={6} align={lying ? "center" : m.side < 0 ? "flex-start" : "flex-end"} motion={lying ? { dx: 0, dy: m.side * 30 } : { dx: m.side * 40, dy: 0 }} style={{ width: m.w }} />
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </FitBox>
    </Stage>
  );
};
