import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { jitter, stepFrame, STEP_FPS } from "../paper/stopMotion";
import { colors, fonts, onPaper, shadowFilter } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H, STAGE_W } from "./Stage";
import { enterFor } from "./timing";

const SLAM = [1.7, 1.25, 0.94, 1];

export const Stamp: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const text = str(props.text, "…").toUpperCase();
  const fit = fitText(text, { maxWidth: 700, maxLines: 3, max: 150, min: 56 });
  const at = enterFor("text", items, from, to);
  const local = frame - at;
  const step = local < 0 ? -1 : Math.round(stepFrame(local) / (30 / STEP_FPS));
  const scale = step < 0 ? 0 : SLAM[Math.min(step, SLAM.length - 1)];
  const ink = onPaper[accent];

  return (
    <Stage>
      <PaperShape kind="square" color="cream" size={1} w={860} h={640} x={(STAGE_W - 860) / 2} y={(STAGE_H - 640) / 2} rotate={3} seed="stamp-sheet" wobble={0.3} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            opacity: scale === 0 ? 0 : 1,
            transform: `rotate(${-7 + jitter("stamp", frame, 0.6)}deg) scale(${scale})`,
            filter: shadowFilter,
          }}
        >
          <div style={{ background: colors[accent], padding: 26 }}>
            <div
              style={{
                border: `8px solid ${ink}`,
                padding: "22px 40px",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                fontFamily: fonts.text,
                fontWeight: 800,
                fontSize: fit.size,
                lineHeight: 1.02,
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
