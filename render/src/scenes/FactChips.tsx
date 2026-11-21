import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperShape } from "../paper/PaperShape";
import { enterScale } from "../paper/stopMotion";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const OFFSETS = [0, 120, 30, 150, 10, 110];
const PIN = 56;

export const FactChips: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const chips = strList(props.chips, 6);
  const shown = chips.length > 0 ? chips : ["…"];
  const rowH = STAGE_H / shown.length;
  const max = shown.length <= 3 ? 84 : shown.length <= 4 ? 72 : 60;

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          inset: "20px 0",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-evenly",
        }}
      >
        {shown.map((chip, i) => {
          const fit = fitText(chip, { maxWidth: 820, maxLines: rowH > 220 ? 2 : 1, max, min: 44 });
          const at = enterFor(`chips.${i}`, items, from, to);
          const visible = enterScale(frame, at) > 0;
          return (
            <div
              key={`chip-${i}`}
              style={{
                position: "relative",
                marginLeft: 70 + OFFSETS[i % OFFSETS.length] * (fit.lines.length > 1 ? 0.3 : 1),
                display: "flex",
                alignItems: "center",
              }}
            >
              <div style={{ position: "relative", width: PIN, height: PIN, marginRight: 22, flex: "none" }}>
                <PaperShape
                  kind={i % 2 === 0 ? "circle" : "square"}
                  color={accent}
                  size={PIN}
                  rotate={i % 2 === 0 ? 0 : 14}
                  enterAt={at}
                  seed={`chip-pin-${i}`}
                  style={{ opacity: visible ? 1 : 0 }}
                />
              </div>
              <Strips lines={fit.lines} size={fit.size} enterAt={at + 1} align="flex-start" seed={`chip-${i}`} />
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
