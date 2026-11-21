import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { accentCycle, AccentColor, colors, fonts } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { commonFit } from "./FactChips";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
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
  const rival = rivalOf(accent);
  const left = str(props.left, "…").slice(0, 24);
  const right = str(props.right, "…").slice(0, 24);
  const [leftFit, rightFit] = commonFit([left, right], PANEL_W - 10, 2, 76, 40, true);
  const top = areaTop(props);
  const labelH = Math.max(stripsHeight(leftFit.lines.length, leftFit.size, 8), stripsHeight(rightFit.lines.length, rightFit.size, 8));
  const panelH = Math.min(620, STAGE_H - top - labelH - 60);
  const total = panelH + 30 + labelH;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);
  const leftAt = enterFor("left", items, from, to);
  const rightAt = Math.max(leftAt + 6, enterFor("right", items, from, to));
  const vsAt = rightAt + 6;
  const vs = frame < vsAt ? 0 : spring({ frame: frame - vsAt, fps: 30, config: { damping: 9, stiffness: 200, mass: 0.6 } });
  const vsOpacity = interpolate(frame - vsAt, [0, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const picto = Math.min(PANEL_W - 70, panelH - 120, 320);
  const sides = [
    { x: BOX_L, color: accent, name: props.left_picto, fit: leftFit, at: leftAt, panelAt: -3, dx: -420, tilt: -2.5, key: "left" },
    { x: BOX_L + PANEL_W + GUTTER, color: rival, name: props.right_picto, fit: rightFit, at: rightAt, panelAt: 1, dx: 420, tilt: 2.5, key: "right" },
  ];

  return (
    <Stage>
      {sides.map((s) => (
        <React.Fragment key={s.key}>
          <PaperShape
            kind="square"
            color={s.color}
            size={1}
            w={PANEL_W}
            h={panelH}
            x={s.x}
            y={y0}
            rotate={s.tilt}
            enterAt={s.panelAt}
            seed={`vs-panel-${s.key}`}
            float={2.5}
            motion={{ dx: s.dx, dy: 0, spin: s.tilt * 3, from: 0.96 }}
          />
          <div style={{ position: "absolute", left: s.x + PANEL_W / 2 - picto * 0.62, top: y0 + panelH / 2 - picto * 0.62 - 10, width: picto * 1.24, height: picto * 1.24 }}>
            <PaperShape kind="circle" color="cream" size={picto * 1.24} enterAt={s.at + 3} seed={`vs-disc-${s.key}`} float={2} motion={{ dx: s.dx * 0.5, dy: 0, spin: 0, from: 0.9 }} />
            {pictoName(s.name) ? (
              <Picto name={s.name} size={picto} x={picto * 0.12} y={picto * 0.12} enterAt={s.at + 5} rotate={s.tilt * 2} seed={`vs-picto-${s.key}`} motion={{ dx: s.dx * 0.4, dy: 0 }} />
            ) : null}
          </div>
          <div style={{ position: "absolute", left: s.x - 10, width: PANEL_W + 20, top: y0 + panelH + 30, display: "flex", justifyContent: "center" }}>
            <Strips lines={s.fit.lines} size={s.fit.size} enterAt={s.at + 6} seed={`vs-label-${s.key}`} gap={8} motion={{ dx: s.dx * 0.3, dy: 0 }} />
          </div>
        </React.Fragment>
      ))}
      <div
        style={{
          position: "absolute",
          left: BOX_CX - 95,
          top: y0 + panelH / 2 - 95,
          width: 190,
          height: 190,
          opacity: vsOpacity,
          transform: `scale(${0.9 + 0.1 * vs}) rotate(${-8 + (1 - vs) * 30}deg)`,
        }}
      >
        <PaperShape kind="circle" color="ink" size={190} seed="vs-badge" float={2}>
          <span style={{ fontFamily: fonts.brand, fontWeight: 900, fontSize: 76, lineHeight: 1, color: colors.cream, letterSpacing: -2, marginTop: 4 }}>VS</span>
        </PaperShape>
      </div>
    </Stage>
  );
};
