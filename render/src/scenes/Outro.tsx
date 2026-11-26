import React from "react";
import { nextAccent } from "../theme";
import { spring, useCurrentFrame } from "remotion";
import { Character, CUT_Y, sizeForHead, VIEW } from "../mascot/Character";
import { PaperStrip, stripHeight } from "../paper/PaperStrip";
import { useAccent } from "./accent";
import { Backdrop } from "./Backdrop";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_R, BOX_W, Stage, STAGE_H, STAGE_W } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { FitBox } from "./FitBox";

export const splitOutro = (text: string): { head: string; tail: string } => {
  const cut = text.indexOf(":");
  if (cut > 0) return { head: text.slice(0, cut).trim(), tail: text.slice(cut + 1).trim() };
  const words = text.split(" ").filter((w) => w.length > 0);
  if (words.length < 4) return { head: text, tail: "" };
  return { head: words.slice(0, -2).join(" "), tail: words.slice(-2).join(" ") };
};

const HEAD_PX = 190;
const MASCOT = sizeForHead(HEAD_PX);
const UNIT = MASCOT / VIEW.h;
const VISIBLE = (CUT_Y - VIEW.y) * UNIT;

export const Outro: React.FC<SceneProps> = ({ props }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const text = str(props.text, "À suivre");
  const { head, tail } = splitOutro(text);
  const headFit = fitText(head, { maxWidth: BOX_W, maxLines: 3, max: 88, min: 52 });
  const tailFit = fitText(tail, { maxWidth: BOX_W - 30, maxLines: 2, max: 136, min: 60 });
  const top = areaTop(props);
  const textH = stripsHeight(headFit.lines.length, headFit.size) + 26 + tailFit.lines.length * (stripHeight(tailFit.size) + 14);
  const room = STAGE_H - top - VISIBLE - 50;
  const y0 = top + Math.max(0, (room - textH) / 2);
  const rise = spring({ frame: frame - 10, fps: 30, config: { damping: 12, stiffness: 120 } });
  const wave = 0.012 * Math.sin((frame / 30) * 5);

  return (
    <Stage>
      <Backdrop color={nextAccent(accent)} size={620} cx={BOX_R + 60} cy={y0 + textH * 0.55} seed="outro-disk" turn={10} />
      <FitBox area={{ left: BOX_L, top: top + 10, width: BOX_W, height: room }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 26, width: BOX_W }}>
        <Strips lines={headFit.lines} size={headFit.size} enterAt={2} align="flex-start" seed="outro-head" motion={{ dx: -60, dy: 0 }} />
        {tailFit.lines.map((line, i) => (
          <PaperStrip
            key={`outro-tail-${i}`}
            text={line}
            color="ink"
            fontSize={tailFit.size}
            enterAt={8 + i * 3}
            rotate={i % 2 === 0 ? 2 : -1.5}
            seed={`outro-tail-${i}`}
            motion={{ dx: 80, dy: 0, spin: 6 }}
            style={{ marginLeft: 30 }}
          />
        ))}
      </div>
      </FitBox>
      <div style={{ position: "absolute", left: 0, top: 0, width: STAGE_W, height: STAGE_H, overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, transform: `translateY(${(1 - rise) * 260}px)` }}>
          <Character
            size={MASCOT}
            pose="content"
            body="blue"
            seed="outro"
            lift={wave > 0 ? wave : 0}
            style={{ left: BOX_R - 260 + VIEW.x * UNIT, top: STAGE_H - VISIBLE }}
          />
        </div>
      </div>
    </Stage>
  );
};
