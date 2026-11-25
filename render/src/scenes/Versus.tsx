import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { hasVisual, Picto } from "../pictos/Picto";
import { accentCycle, AccentColor, colors, fonts } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { commonFit } from "./FactChips";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { areaFor, FitBox } from "./FitBox";
import { tween } from "../paper/motion";
import { useBeat } from "./beats";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const GUTTER = 56;
const PANEL_W = (BOX_W - GUTTER) / 2;

export const rivalOf = (accent: AccentColor): AccentColor => {
  const i = accentCycle.indexOf(accent);
  return accentCycle[(i + 2) % accentCycle.length];
};

export const Versus: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const beat = useBeat();
  const badgePop = beat && beat.index % 2 === 0 ? beat.wave : 0;
  const nudge = beat && beat.index % 2 === 1 ? beat.wave : 0;
  const rival = rivalOf(accent);
  const left = str(props.left, "…").slice(0, 24);
  const right = str(props.right, "…").slice(0, 24);
  const [leftFit, rightFit] = commonFit([left, right], PANEL_W - 10, 2, 80, 48, true);
  const top = areaTop(props);
  const labelH = Math.max(stripsHeight(leftFit.lines.length, leftFit.size, 8), stripsHeight(rightFit.lines.length, rightFit.size, 8));
  const panelH = 620;
  const total = panelH + 30 + labelH;
  const leftAt = enterFor("left", items, from, to);
  const rightAt = Math.max(leftAt + 6, enterFor("right", items, from, to));
  const vsAt = rightAt + 6;
  const vs = frame < vsAt ? 0 : spring({ frame: frame - vsAt, fps: 30, config: { damping: 9, stiffness: 200, mass: 0.6 } });
  const vsOpacity = interpolate(frame - vsAt, [0, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const picto = Math.min(PANEL_W - 70, panelH - 120, 320);
  const sides = [
    { x: 0, color: accent, name: props.left_picto, fit: leftFit, at: leftAt, panelAt: -3, dx: -420, tilt: -2.5, key: "left" },
    { x: PANEL_W + GUTTER, color: rival, name: props.right_picto, fit: rightFit, at: rightAt, panelAt: 1, dx: 420, tilt: 2.5, key: "right" },
  ];

  return (
    <Stage>
      <FitBox area={areaFor(top + 10, BOX_L, BOX_W)}>
        <div style={{ position: "relative", width: BOX_W, height: total }}>
          {sides.map((s) => {
            const come = tween(frame, s.at, 12);
            return (
              <div
                key={s.key}
                style={{
                  position: "absolute",
                  left: s.x,
                  top: 0,
                  width: PANEL_W,
                  height: total,
                  opacity: 0.42 + 0.58 * come,
                  transform: `translateX(${(s.key === "left" ? 22 : -22) * nudge}px) scale(${(0.86 + 0.14 * come) * (1 + 0.04 * nudge)})`,
                  transformOrigin: `${s.key === "left" ? "30%" : "70%"} 45%`,
                }}
              >
                <PaperShape
                  kind="square"
                  color={s.color}
                  size={1}
                  w={PANEL_W}
                  h={panelH}
                  rotate={s.tilt}
                  enterAt={s.panelAt}
                  seed={`vs-panel-${s.key}`}
                  float={3}
                  motion={{ dx: s.dx, dy: 0, spin: s.tilt * 3, from: 0.96 }}
                />
                {hasVisual(s.name) ? (
                  <div style={{ position: "absolute", left: PANEL_W / 2 - picto * 0.62, top: panelH / 2 - picto * 0.62 - 10, width: picto * 1.24, height: picto * 1.24 }}>
                    <PaperShape kind="circle" color="cream" size={picto * 1.24} enterAt={s.at + 2} seed={`vs-disc-${s.key}`} float={2} motion={{ dx: 0, dy: 0, spin: 0, from: 0.9 }} />
                    <Picto name={s.name} size={picto} x={picto * 0.12} y={picto * 0.12} enterAt={s.at + 4} rotate={s.tilt * 2} seed={`vs-picto-${s.key}`} motion={{ dx: s.dx * 0.3, dy: 0 }} react={false} />
                  </div>
                ) : null}
                <div style={{ position: "absolute", left: -10, width: PANEL_W + 20, top: panelH + 30, display: "flex", justifyContent: "center" }}>
                  <Strips lines={s.fit.lines} size={s.fit.size} enterAt={s.at + 6} seed={`vs-label-${s.key}`} gap={8} motion={{ dx: s.dx * 0.3, dy: 0 }} />
                </div>
              </div>
            );
          })}
          <div
            style={{
              position: "absolute",
              left: BOX_W / 2 - 95,
              top: panelH / 2 - 95,
              width: 190,
              height: 190,
              opacity: vsOpacity,
              transform: `scale(${(0.9 + 0.1 * vs) * (1 + 0.28 * badgePop)}) rotate(${-8 + (1 - vs) * 30 + 14 * badgePop}deg)`,
            }}
          >
            <PaperShape kind="circle" color="ink" size={190} seed="vs-badge" float={2}>
              <span style={{ fontFamily: fonts.brand, fontWeight: 900, fontSize: 76, lineHeight: 1, color: colors.cream, letterSpacing: -2, marginTop: 4 }}>VS</span>
            </PaperShape>
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
