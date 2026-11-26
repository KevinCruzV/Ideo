import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { Sheet } from "../paper/Sheet";
import { layout } from "../theme";
import { str } from "./coerce";
import { Kicker } from "./Kicker";
import { framingAt, PUNCH_ORIGIN_Y } from "./punch";
import { BOX_CX, Stage } from "./Stage";

const SAFE_SHIFT = layout.safeCenterX - BOX_CX;

export const EXIT_FRAMES = 6;
export const DRIFT_SCALE = 0.03;

export const SceneFrame: React.FC<{ props: Record<string, unknown>; duration: number; last: boolean; index?: number; cuts?: number[]; children: React.ReactNode }> = ({
  props,
  duration,
  last,
  index = 0,
  cuts = [],
  children,
}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, duration);
  const scale = layout.safeScale * (1 + DRIFT_SCALE * Math.min(1, frame / span));
  const exit = last ? 0 : interpolate(frame, [span - EXIT_FRAMES, span], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const kicker = str(props.kicker);
  const f = framingAt(cuts, frame);
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: 1 - exit,
        transform: `translate(${f.x}px, ${f.y}px) rotate(${f.r}deg) scale(${1 + f.s})`,
        transformOrigin: `${layout.safeCenterX}px ${PUNCH_ORIGIN_Y}px`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `translateX(${SAFE_SHIFT - 70 * exit * exit}px) scale(${scale})`,
          transformOrigin: `${BOX_CX}px ${(layout.stageTop + layout.stageBottom) / 2}px`,
        }}
      >
        <Sheet index={index} />
        {children}
        {kicker ? (
          <Stage>
            <Kicker text={kicker} />
          </Stage>
        ) : null}
      </div>
    </div>
  );
};
