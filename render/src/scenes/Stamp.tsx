import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { PaperBacking } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { enterFor } from "./timing";
import { useBeat } from "./beats";

const SHEET_W = BOX_W - 20;

export const Stamp: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const beat = useBeat();
  const press = beat ? beat.wave : 0;
  const text = str(props.text, "…").toUpperCase();
  const fit = fitText(text, { maxWidth: SHEET_W - 200, maxLines: 3, max: 136, min: 56 });
  const at = enterFor("text", items, from, to);
  const local = frame - at;
  const top = areaTop(props);
  const sheetH = Math.min(760, STAGE_H - top - 70);
  const sheetY = top + (STAGE_H - top - sheetH) / 2;
  const slam = local < 0 ? 0 : spring({ frame: local, fps: 30, config: { damping: 11, stiffness: 260, mass: 0.6 } });
  const scale = local < 0 ? 1.5 : 1.5 - 0.5 * slam;
  const opacity = interpolate(local, [0, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const thump = (local >= 0 && local < 10 ? Math.sin((local / 10) * Math.PI) * (1 - local / 10) * 10 : 0) + 7 * press;
  const ink = onPaper[accent];
  const lines = [0.22, 0.34, 0.46, 0.58, 0.7, 0.82];

  return (
    <Stage>
      <div style={{ position: "absolute", inset: 0, transform: `translateY(${thump}px)` }}>
        <PaperShape kind="square" color="cream" size={1} w={SHEET_W} h={sheetH} x={BOX_CX - SHEET_W / 2} y={sheetY} rotate={2} seed="stamp-sheet" float={2} spin={0.2} motion={{ dy: 80, spin: 6 }}>
          <div style={{ position: "absolute", inset: 0 }}>
            {lines.map((l, i) => (
              <div
                key={`rule-${i}`}
                style={{ position: "absolute", left: 70, right: i % 3 === 2 ? 260 : 70, top: `${l * 100}%`, height: 10, background: "rgba(31,26,20,.09)" }}
              />
            ))}
          </div>
        </PaperShape>
        <Picto name={props.picto} size={190} x={BOX_CX - SHEET_W / 2 - 20} y={sheetY - 50} rotate={-8} enterAt={4} />
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: sheetY, height: sheetH, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ position: "relative", left: BOX_CX - 540, opacity, transform: `rotate(${-7 + 2 * press}deg) scale(${scale * (1 - 0.06 * press)})` }}>
          <PaperBacking color={accent} seed="stamp-plate" amount={0.8} />
          <div style={{ position: "relative", padding: 24 }}>
            <div
              style={{
                border: `9px solid ${ink}`,
                padding: "26px 44px 30px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                fontFamily: fonts.text,
                fontWeight: 800,
                fontSize: fit.size,
                lineHeight: 1.12,
                letterSpacing: 2,
                color: ink,
                whiteSpace: "nowrap",
              }}
            >
              {fit.lines.map((line, i) => (
                <span key={`stamp-${i}`}>{line}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Stage>
  );
};
