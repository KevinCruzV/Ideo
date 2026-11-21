import React from "react";
import { useCurrentFrame } from "remotion";
import { enterScale, jitter } from "../paper/stopMotion";
import { colors, fonts, onPaper, shadowFilter } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage } from "./Stage";
import { enterFor } from "./timing";

const BUBBLE_W = 760;
const bubbleClip = "polygon(1% 3%, 99% 0, 100% 96%, 2% 100%)";
const tailClip = "polygon(0 0, 100% 0, 92% 100%)";

export const Mascot: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const fit = fitText(str(props.bubble, "…"), { maxWidth: BUBBLE_W - 60, maxLines: 5, max: 88, min: 46 });
  const at = enterFor("bubble", items, from, to);
  const scale = enterScale(frame, at);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          right: 90,
          bottom: 50,
          width: 360,
          height: 470,
          border: `6px dashed ${colors.ink}`,
          borderRadius: "180px 180px 48px 48px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: fonts.text,
          fontWeight: 800,
          fontSize: 44,
          color: colors.ink,
          transform: `rotate(${jitter("mascot", frame, 0.5)}deg)`,
        }}
      >
        [MASCOTTE]
      </div>
      <div
        style={{
          position: "absolute",
          left: 60,
          top: 50,
          maxWidth: BUBBLE_W,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          opacity: scale === 0 ? 0 : 1,
          transform: `rotate(${-2 + jitter("bubble", frame, 0.6)}deg) scale(${scale})`,
          transformOrigin: "80% 100%",
          filter: shadowFilter,
        }}
      >
        <div
          style={{
            background: colors[accent],
            clipPath: bubbleClip,
            padding: "40px 30px",
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
        <div style={{ flex: "none", marginRight: 110, width: 130, height: 120, background: colors[accent], clipPath: tailClip, marginTop: -2 }} />
      </div>
    </Stage>
  );
};
