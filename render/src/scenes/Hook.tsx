import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { PaperStrip } from "../paper/PaperStrip";
import { stepFrame, STEP_FPS } from "../paper/stopMotion";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText, splitKey } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";

const SLIDE = [-980, -640, -360, -230];
const CIRCLE = 720;
const TEXT_W = 900;

export const Hook: React.FC<SceneProps> = ({ props }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 2, max: 80, min: 52 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 1, max: after ? 160 : 180, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 3, max: 72, min: 48 });
  const step = Math.round(stepFrame(frame) / (30 / STEP_FPS));
  const slideX = SLIDE[Math.min(step, SLIDE.length - 1)];

  return (
    <Stage>
      <PaperShape kind="circle" color={accent} size={CIRCLE} x={slideX} y={0} seed="hook-circle" wobble={0.6} />
      <PaperShape
        kind="square"
        color="cream"
        size={300}
        x={800}
        y={STAGE_H - 380}
        rotate={8}
        enterAt={8}
        seed="hook-square"
      />
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          top: 380,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 22,
        }}
      >
        <Strips lines={head.lines} size={head.size} enterAt={6} align="flex-start" seed="hook-head" tilt={-1} />
        {word.lines.length > 0 ? (
          <PaperStrip
            text={word.lines[0]}
            color={accent}
            fontSize={word.size}
            enterAt={12}
            rotate={1.5}
            seed="hook-key"
            style={{ marginLeft: 24 }}
          />
        ) : null}
        <Strips lines={tail.lines} size={tail.size} enterAt={18} align="flex-start" seed="hook-tail" />
      </div>
    </Stage>
  );
};
