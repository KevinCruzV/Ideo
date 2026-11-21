import React from "react";
import { useCurrentFrame } from "remotion";
import { Character } from "../mascot/Character";
import { hopLift, LAND_FRAMES, poseOf } from "../mascot/pose";
import { enterScale, jitter } from "../paper/stopMotion";
import { colors, fonts, layout, onPaper, shadowFilter } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { enterFor } from "./timing";

export const CHARACTER_SIZE = 600;
const CHARACTER_LEFT = 40;
const CHARACTER_BOTTOM = 16;
const BUBBLE_LEFT = 400;
const BUBBLE_W = layout.width - layout.marginSide - BUBBLE_LEFT;
const BUBBLE_PAD_X = 30;
const TAIL_TIP_Y = 520;
const bubbleClip = "polygon(1% 3%, 99% 0, 100% 96%, 2% 100%)";
const tailClip = "polygon(22% 0, 100% 0, 0 100%)";

export const Mascot: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const pose = poseOf(props.pose);
  const fit = fitText(str(props.bubble, "…"), {
    maxWidth: BUBBLE_W - BUBBLE_PAD_X * 2,
    maxLines: 4,
    max: 72,
    min: 44,
  });
  const at = enterFor("bubble", items, from, to);
  const scale = enterScale(frame, at);
  const lift = hopLift(frame, at + LAND_FRAMES);

  return (
    <Stage>
      <Character
        size={CHARACTER_SIZE}
        pose={pose}
        body="ink"
        lift={lift}
        style={{ left: CHARACTER_LEFT, top: STAGE_H - CHARACTER_SIZE - CHARACTER_BOTTOM }}
      />
      <div
        style={{
          position: "absolute",
          left: BUBBLE_LEFT,
          bottom: STAGE_H - TAIL_TIP_Y,
          maxWidth: BUBBLE_W,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          opacity: scale === 0 ? 0 : 1,
          transform: `rotate(${3 + jitter("bubble", frame, 0.6)}deg) scale(${scale})`,
          transformOrigin: "0% 100%",
          filter: shadowFilter,
        }}
      >
        <div
          style={{
            background: colors[accent],
            clipPath: bubbleClip,
            padding: `36px ${BUBBLE_PAD_X}px`,
            fontFamily: fonts.text,
            fontWeight: 800,
            fontSize: fit.size,
            lineHeight: 1.12,
            color: onPaper[accent],
            whiteSpace: "nowrap",
          }}
        >
          {fit.lines.map((line, i) => (
            <div key={`bubble-${i}`}>{line}</div>
          ))}
        </div>
        <div style={{ flex: "none", marginLeft: 40, width: 120, height: 84, background: colors[accent], clipPath: tailClip, marginTop: -2 }} />
      </div>
    </Stage>
  );
};
