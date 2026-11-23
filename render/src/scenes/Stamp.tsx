import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { PaperBacking } from "../paper/PaperStrip";
import { contrastPaper, Picto } from "../pictos/Picto";
import { colors, fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { str, variantOf } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { enterFor } from "./timing";
import { useBeat } from "./beats";
import { PaperStrip } from "../paper/PaperStrip";
import { Strips } from "./Strips";
import { restTilt } from "../paper/motion";

const SHEET_W = BOX_W - 20;

const StampRubber: React.FC<SceneProps> = ({ props, items, from, to }) => {
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
        {local < 6 ? (
          <div style={{ position: "absolute", left: "50%", top: "50%", transform: `translate(calc(-50% + ${BOX_CX - 540}px), -50%) rotate(-7deg)`, opacity: 0.16 * (1 - Math.max(0, local) / 6) }}>
            <div style={{ padding: 24 }}>
              <div
                style={{
                  border: `9px dashed ${colors.ink}`,
                  padding: "26px 44px 30px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  fontFamily: fonts.text,
                  fontWeight: 800,
                  fontSize: fit.size,
                  lineHeight: 1.12,
                  letterSpacing: 2,
                  color: colors.ink,
                  whiteSpace: "nowrap",
                }}
              >
                {fit.lines.map((l, i) => (
                  <span key={`ghost-${i}`}>{l}</span>
                ))}
              </div>
            </div>
          </div>
        ) : null}
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

const StampBanner: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const beat = useBeat();
  const press = beat ? beat.wave : 0;
  const text = str(props.text, "…").toUpperCase();
  const fit = fitText(text, { maxWidth: BOX_W - 60, maxLines: 3, max: 118, min: 60 });
  const at = enterFor("text", items, from, to);
  const top = areaTop(props);
  const room = STAGE_H - top;
  return (
    <Stage>
      <Picto name={props.picto} size={240} x={BOX_CX + BOX_W / 2 - 250} y={top + 30} rotate={10} enterAt={at + 4} />
      <div
        style={{
          position: "absolute",
          left: BOX_CX - BOX_W / 2,
          top: top + room * 0.24,
          width: BOX_W,
          display: "flex",
          justifyContent: "center",
          transform: `rotate(${-4 + 2 * press}deg) scale(${1 + 0.05 * press})`,
        }}
      >
        <Strips lines={fit.lines} size={fit.size} color={accent} enterAt={at} stagger={4} seed="stamp-banner" tilt={-1} gap={18} motion={{ dx: -120, dy: 0, spin: 10 }} />
      </div>
      <PaperShape kind="strip" color="ink" size={1} w={BOX_W * 0.55} h={26} x={BOX_CX - BOX_W * 0.27} y={top + room * 0.24 + fit.lines.length * fit.size * 1.6 + 60} rotate={-3} enterAt={at + 10} seed="stamp-underline" motion={{ dx: -200, dy: 0 }} />
    </Stage>
  );
};

export const NOTE_PAPERS = ["yellow", "blue", "red", "cream"] as const;

const StampNote: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const beat = useBeat();
  const press = beat ? beat.wave : 0;
  const text = str(props.text, "…");
  const side = Math.min(760, BOX_W - 60);
  const fit = fitText(text, { maxWidth: side - 140, maxLines: 4, max: 96, min: 52 });
  const at = enterFor("text", items, from, to);
  const top = areaTop(props);
  const y = top + (STAGE_H - top - side) / 2;
  const x = BOX_CX - side / 2;
  const tilt = -3 + restTilt("stamp-note", 2);
  const paper = contrastPaper(props.picto, NOTE_PAPERS);
  return (
    <Stage>
      <div style={{ position: "absolute", inset: 0, transform: `rotate(${2 * press}deg)` }}>
        <PaperShape kind="square" color={paper} size={side} x={x} y={y} rotate={tilt} enterAt={at - 2} seed="stamp-note" float={3} motion={{ dy: 120, spin: -8 }}>
          <div
            style={{
              width: side - 140,
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-start",
              fontFamily: fonts.text,
              fontWeight: 800,
              fontSize: fit.size,
              lineHeight: 1.15,
              whiteSpace: "nowrap",
              color: onPaper[paper],
              transform: `scale(${1 + 0.04 * press})`,
            }}
          >
            {fit.lines.map((line, i) => (
              <span key={`note-${i}`}>{line}</span>
            ))}
          </div>
        </PaperShape>
        <PaperShape kind="strip" color="cream" size={1} w={210} h={64} x={x - 40} y={y - 20} rotate={-28} enterAt={at + 4} seed="stamp-tape-a" shadow={false} style={{ opacity: 0.85 }} />
        <PaperShape kind="strip" color="cream" size={1} w={210} h={64} x={x + side - 170} y={y - 20} rotate={24} enterAt={at + 6} seed="stamp-tape-b" shadow={false} style={{ opacity: 0.85 }} />
        <Picto name={props.picto} size={200} x={x + side - 150} y={y + side - 170} rotate={-8} enterAt={at + 8} />
      </div>
    </Stage>
  );
};

export const STAMP_VARIANTS = [StampRubber, StampBanner, StampNote] as const;

export const Stamp: React.FC<SceneProps> = (scene) => {
  const Variant = STAMP_VARIANTS[variantOf(scene.props.variant, STAMP_VARIANTS.length)];
  return <Variant {...scene} />;
};
