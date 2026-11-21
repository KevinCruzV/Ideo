import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const TILTS = [-6, 4, -3, 7, -5];

export const StackList: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const entries = strList(props.items, 5);
  const shown = entries.length > 0 ? entries : ["…"];
  const rowH = Math.min(240, STAGE_H / shown.length);
  const badge = Math.min(130, rowH * 0.62);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: Math.max(16, rowH * 0.16),
          paddingLeft: 64,
        }}
      >
        {shown.map((entry, i) => {
          const at = enterFor(`items.${i}`, items, from, to);
          const fit = fitText(entry, { maxWidth: 790, maxLines: 2, max: shown.length <= 3 ? 76 : 64, min: 44 });
          return (
            <div key={`stack-${i}`} style={{ display: "flex", alignItems: "center", gap: 30 }}>
              <div style={{ position: "relative", width: badge, height: badge, flex: "none" }}>
                <PaperShape
                  kind="square"
                  color={accent}
                  size={badge}
                  rotate={TILTS[i % TILTS.length]}
                  enterAt={at}
                  seed={`stack-badge-${i}`}
                >
                  <span
                    style={{
                      fontFamily: fonts.text,
                      fontWeight: 800,
                      fontSize: badge * 0.62,
                      lineHeight: 1,
                      color: onPaper[accent],
                    }}
                  >
                    {i + 1}
                  </span>
                </PaperShape>
              </div>
              <Strips lines={fit.lines} size={fit.size} enterAt={at + 2} align="flex-start" seed={`stack-${i}`} gap={8} />
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
