import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { Character, CUT_Y, sizeForHead, VIEW } from "../mascot/Character";
import { hopLift, LAND_FRAMES, poseOf } from "../mascot/pose";
import { drift } from "../paper/motion";
import { PaperBacking } from "../paper/PaperStrip";
import { colors, fonts, onPaper, shade, SHADOW_X, SHADOW_Y } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { BOX_R, Stage, STAGE_H, STAGE_W } from "./Stage";
import { enterFor } from "./timing";

const HEAD_PX = 300;
const HEAD_X = 250;
export const CHARACTER_SIZE = sizeForHead(HEAD_PX);
const UNIT = CHARACTER_SIZE / VIEW.h;
const CHARACTER_LEFT = HEAD_X + VIEW.x * UNIT;
const CHARACTER_TOP = STAGE_H - (CUT_Y - VIEW.y) * UNIT;
const BUBBLE_LEFT = 360;
const BUBBLE_W = BOX_R - BUBBLE_LEFT;
const BUBBLE_PAD_X = 34;
const TAIL_TIP_Y = 560;
const tailClip = "polygon(22% 0, 100% 0, 0 100%)";

export const Mascot: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const pose = poseOf(props.pose);
  const fit = fitText(str(props.bubble, "…"), {
    maxWidth: BUBBLE_W - BUBBLE_PAD_X * 2 + 36,
    maxLines: 4,
    max: 74,
    min: 44,
  });
  const at = enterFor("bubble", items, from, to);
  const local = frame - at;
  const pop = local < 0 ? 0 : spring({ frame: local, fps: 30, config: { damping: 12, stiffness: 170, mass: 0.7 } });
  const scale = 0.9 + 0.1 * pop;
  const opacity = interpolate(local, [0, 4], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lift = hopLift(frame, at + LAND_FRAMES);
  const d = drift("bubble", frame, 3, 0.4);
  const enterBody = spring({ frame: frame + 4, fps: 30, config: { damping: 14, stiffness: 120 } });

  return (
    <Stage>
      <div style={{ position: "absolute", left: 0, top: 0, width: STAGE_W, height: STAGE_H, overflow: "hidden" }}>
        <div style={{ position: "absolute", inset: 0, transform: `translateY(${(1 - enterBody) * 160}px)` }}>
          <Character size={CHARACTER_SIZE} pose={pose} body="blue" lift={lift} style={{ left: CHARACTER_LEFT, top: CHARACTER_TOP }} />
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: BUBBLE_LEFT,
          bottom: STAGE_H - TAIL_TIP_Y,
          width: BUBBLE_W,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          opacity,
          transform: `translate(${d.x}px, ${d.y + (1 - pop) * 30}px) rotate(${2.5 + d.r + (1 - pop) * 6}deg) scale(${scale})`,
          transformOrigin: "10% 100%",
        }}
      >
        <div style={{ position: "relative", alignSelf: "stretch" }}>
          <PaperBacking color={accent} seed="bubble" amount={0.8} />
          <div
            style={{
              position: "relative",
              padding: `34px ${BUBBLE_PAD_X}px 40px`,
              fontFamily: fonts.text,
              fontWeight: 800,
              fontSize: fit.size,
              lineHeight: 1.16,
              color: onPaper[accent],
              whiteSpace: "nowrap",
            }}
          >
            {fit.lines.map((line, i) => (
              <div key={`bubble-${i}`}>{line}</div>
            ))}
          </div>
        </div>
        <div style={{ position: "relative", flex: "none", marginLeft: 40, width: 120, height: 84, marginTop: -2 }}>
          <div style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X}px, ${SHADOW_Y}px)`, background: shade, clipPath: tailClip }} />
          <div style={{ position: "absolute", inset: 0, background: colors[accent], clipPath: tailClip }} />
        </div>
      </div>
    </Stage>
  );
};
