import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { layout } from "../theme";
import { str } from "./coerce";
import { Kicker } from "./Kicker";
import { BOX_CX, Stage } from "./Stage";

export const EXIT_FRAMES = 6;
export const DRIFT_SCALE = 0.03;

export const SceneFrame: React.FC<{ props: Record<string, unknown>; duration: number; last: boolean; children: React.ReactNode }> = ({
  props,
  duration,
  last,
  children,
}) => {
  const frame = useCurrentFrame();
  const span = Math.max(1, duration);
  const scale = 1 + DRIFT_SCALE * Math.min(1, frame / span);
  const exit = last ? 0 : interpolate(frame, [span - EXIT_FRAMES, span], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const kicker = str(props.kicker);
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity: 1 - exit,
        transform: `translateX(${-70 * exit * exit}px) scale(${scale})`,
        transformOrigin: `${BOX_CX}px ${(layout.stageTop + layout.stageBottom) / 2}px`,
      }}
    >
      {children}
      {kicker ? (
        <Stage>
          <Kicker text={kicker} />
        </Stage>
      ) : null}
    </div>
  );
};
