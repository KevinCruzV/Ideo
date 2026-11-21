import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { PaperStrip } from "../paper/PaperStrip";
import { tween as ease } from "../paper/motion";
import { AccentColor, colors, fonts, onPaper, shadow } from "../theme";
import { useAccent } from "./accent";
import { str, strList } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, Stage, STAGE_H, STAGE_W } from "./Stage";
import { stateIndex, stateTimes } from "./timing";

type ObjectKind = "screen" | "board" | "jar" | "door" | "scale";

const KINDS: ObjectKind[] = ["screen", "board", "jar", "door", "scale"];
const ALIASES: Record<string, ObjectKind> = {
  ecran: "screen",
  écran: "screen",
  tableau: "board",
  bocal: "jar",
  pot: "jar",
  porte: "door",
  balance: "scale",
};

export const objectKind = (value: unknown): ObjectKind => {
  const key = str(value).toLowerCase();
  return (KINDS as string[]).includes(key) ? (key as ObjectKind) : ALIASES[key] ?? "screen";
};

const CX = BOX_CX;

const tween = (frame: number, at: number, prev: number, next: number): number => prev + (next - prev) * ease(frame, at, 16);

type Look = { accent: AccentColor; index: number; count: number; label: string; changedAt: number; frame: number; prevIndex: number };

const Swap: React.FC<{ at: number; children: React.ReactNode }> = ({ at, children }) => {
  const frame = useCurrentFrame();
  const t = ease(frame, at, 10);
  return (
    <div style={{ opacity: Math.min(1, t * 2), transform: `translateY(${(1 - t) * 30}px) scale(${0.92 + 0.08 * t})`, display: "flex", flexDirection: "column", alignItems: "center" }}>
      {children}
    </div>
  );
};

const InnerText: React.FC<{ text: string; width: number; color: string; max: number; at: number }> = ({ text, width, color, max, at }) => {
  const fit = fitText(text, { maxWidth: width, maxLines: 3, max, min: 44 });
  return (
    <Swap key={`${text}-${at}`} at={at}>
      {fit.lines.map((line, i) => (
        <span
          key={`line-${i}`}
          style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: fit.size, lineHeight: 1.1, color, whiteSpace: "nowrap" }}
        >
          {line}
        </span>
      ))}
    </Swap>
  );
};

const Caption: React.FC<{ look: Look; top: number }> = ({ look, top }) => {
  const fit = fitText(look.label, { maxWidth: 886, maxLines: 1, max: 72, min: 40 });
  if (fit.lines.length === 0) return null;
  return (
    <div key={`cap-${look.index}`} style={{ position: "absolute", left: 0, right: 0, top, display: "flex", justifyContent: "center" }}>
      <PaperStrip text={fit.lines[0]} fontSize={fit.size} enterAt={look.changedAt} seed={`os-cap-${look.index}`} rotate={look.index % 2 ? 1.5 : -1.5} />
    </div>
  );
};

const Pips: React.FC<{ look: Look; top: number }> = ({ look, top }) => {
  if (look.count < 2) return null;
  const size = 34;
  const gap = 22;
  const total = look.count * size + (look.count - 1) * gap;
  return (
    <>
      {Array.from({ length: look.count }, (_, i) => (
        <PaperShape
          key={`pip-${i}`}
          kind="circle"
          color={i <= look.index ? look.accent : "cream"}
          size={size}
          x={CX - total / 2 + i * (size + gap)}
          y={top}
        />
      ))}
    </>
  );
};

const Screen: React.FC<{ look: Look; board?: boolean }> = ({ look, board }) => {
  const w = 860;
  const h = 560;
  const x = CX - w / 2;
  const y = 70;
  const innerColor = board ? colors.ink : colors[look.accent];
  const textColor = board ? colors.cream : onPaper[look.accent];
  return (
    <>
      {board ? (
        <>
          <PaperShape kind="square" color="ink" size={1} w={w} h={h} x={x} y={y} rotate={-1} seed="board" float={1.5}>
            <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <InnerText text={look.label} width={w - 120} color={textColor} max={110} at={look.changedAt} />
            </div>
          </PaperShape>
          <PaperShape kind="strip" color={look.accent} size={70} x={x - 40} y={y - 20} rotate={-30} />
          <PaperShape kind="strip" color={look.accent} size={70} x={x + w - 130} y={y - 20} rotate={28} />
          <PaperShape kind="strip" color="cream" size={1} w={200} h={36} x={CX - 100} y={y + h + 30} rotate={2} />
        </>
      ) : (
        <>
          <PaperShape kind="square" color="cream" size={1} w={90} h={120} x={CX - 45} y={y + h - 20} />
          <PaperShape kind="square" color="cream" size={1} w={380} h={44} x={CX - 190} y={y + h + 90} rotate={-1} />
          <PaperShape kind="square" color="ink" size={1} w={w} h={h} x={x} y={y} rotate={-1} seed="screen" float={1.5}>
            <div
              style={{
                position: "absolute",
                inset: 36,
                background: innerColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <InnerText text={look.label} width={w - 140} color={textColor} max={110} at={look.changedAt} />
            </div>
          </PaperShape>
        </>
      )}
      <Pips look={look} top={y + h + 190} />
    </>
  );
};

const Jar: React.FC<{ look: Look }> = ({ look }) => {
  const w = 440;
  const h = 560;
  const x = CX - w / 2;
  const y = 100;
  const ratio = (i: number) => (0.75 * (i + 1)) / Math.max(1, look.count);
  const fill = tween(look.frame, look.changedAt, ratio(look.prevIndex), ratio(look.index));
  const innerH = h - 60;
  return (
    <>
      <PaperShape kind="square" color="cream" size={1} w={w} h={h} x={x} y={y} radius="24px 24px 90px 90px" seed="jar" float={1.5}>
        <div
          style={{
            position: "absolute",
            left: 30,
            right: 30,
            bottom: 30,
            height: innerH * fill,
            background: colors[look.accent],
            borderRadius: "6px 6px 64px 64px",
            boxShadow: shadow,
          }}
        />
      </PaperShape>
      <PaperShape kind="square" color="ink" size={1} w={w + 60} h={70} x={x - 30} y={y - 50} rotate={-2} />
      <Caption look={look} top={y + h + 50} />
      <Pips look={look} top={y + h + 180} />
    </>
  );
};

const Door: React.FC<{ look: Look }> = ({ look }) => {
  const w = 480;
  const h = 680;
  const x = CX - w / 2;
  const y = 50;
  const open = (i: number) => (look.count > 1 ? i / (look.count - 1) : 0);
  const angle = tween(look.frame, look.changedAt, open(look.prevIndex), open(look.index)) * 68;
  return (
    <>
      <PaperShape kind="square" color="ink" size={1} w={w} h={h} x={x} y={y} seed="door-frame" float={1.5}>
        <div style={{ position: "absolute", inset: "30px 30px 0 30px", background: colors.cream, perspective: 1400 }}>
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: colors[look.accent],
              transformOrigin: "left center",
              transform: `rotateY(${-angle}deg)`,
              boxShadow: shadow,
            }}
          >
            <div style={{ position: "absolute", right: 36, top: "52%", width: 46, height: 46, borderRadius: "50%", background: colors.cream, boxShadow: shadow }} />
          </div>
        </div>
      </PaperShape>
      <PaperShape kind="square" color="cream" size={1} w={w + 160} h={36} x={x - 80} y={y + h - 6} rotate={-1} />
      <Caption look={look} top={y + h + 60} />
      <Pips look={look} top={y + h + 190} />
    </>
  );
};

const Scale: React.FC<{ look: Look }> = ({ look }) => {
  const tilt = (i: number) => (look.count > 1 ? (i / (look.count - 1)) * 16 : 0);
  const angle = tween(look.frame, look.changedAt, tilt(look.prevIndex), tilt(look.index));
  const pivotY = 170;
  const half = 340;
  const rad = (angle * Math.PI) / 180;
  const ends = [-1, 1].map((side) => ({ x: CX + side * half * Math.cos(rad), y: pivotY + side * half * Math.sin(rad) }));
  const rope = 190;
  return (
    <>
      <PaperShape kind="square" color="ink" size={1} w={44} h={500} x={CX - 22} y={pivotY} />
      <PaperShape kind="triangle" color="ink" size={1} w={380} h={130} x={CX - 190} y={pivotY + 470} />
      {ends.map((end, i) => (
        <React.Fragment key={`pan-${i}`}>
          <div style={{ position: "absolute", left: end.x - 3, top: end.y, width: 6, height: rope, background: colors.ink }} />
          <PaperShape
            kind="square"
            color={look.accent}
            size={1}
            w={260}
            h={110}
            x={end.x - 130}
            y={end.y + rope - 10}
            radius="0 0 130px 130px"
          />
        </React.Fragment>
      ))}
      <div
        style={{
          position: "absolute",
          left: CX - half - 30,
          top: pivotY - 18,
          width: (half + 30) * 2,
          height: 36,
          background: colors.ink,
          transform: `rotate(${angle}deg)`,
          boxShadow: shadow,
        }}
      />
      <PaperShape kind="circle" color="cream" size={56} x={CX - 28} y={pivotY - 28} />
      <Caption look={look} top={pivotY + 650} />
      <Pips look={look} top={pivotY + 780} />
    </>
  );
};

const EXTENT: Record<ObjectKind, [number, number]> = {
  screen: [70, 854],
  board: [50, 854],
  jar: [50, 874],
  door: [50, 954],
  scale: [150, 984],
};

export const objectOffset = (kind: ObjectKind, top: number): number => {
  const [minY, maxY] = EXTENT[kind];
  return top + Math.max(0, (STAGE_H - top - (maxY - minY)) / 2) - minY;
};

export const ObjectState: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const kind = objectKind(props.object);
  const states = strList(props.states, 6);
  const shown = states.length > 0 ? states : [""];
  const times = stateTimes("states", shown.length, items, from, to);
  const index = stateIndex(times, frame);
  const prevIndex = index > 0 ? index - 1 : 0;
  const look: Look = { accent, index, count: shown.length, label: shown[index], changedAt: index > 0 ? times[index] : 0, frame, prevIndex };
  const body =
    kind === "jar" ? <Jar look={look} /> : kind === "door" ? <Door look={look} /> : kind === "scale" ? <Scale look={look} /> : <Screen look={look} board={kind === "board"} />;
  return (
    <Stage>
      <div style={{ position: "absolute", left: 0, top: objectOffset(kind, areaTop(props)), width: STAGE_W, height: STAGE_H }}>{body}</div>
    </Stage>
  );
};
