import React from "react";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";

const firstText = (props: Record<string, unknown>): string => {
  const preferred = str(props.text) || str(props.label) || str(props.title);
  if (preferred) return preferred;
  for (const [key, value] of Object.entries(props)) {
    if (key === "kicker") continue;
    const s = str(value);
    if (s) return s;
  }
  return "";
};

export const Placeholder: React.FC<SceneProps> = ({ props }) => {
  const fit = fitText(firstText(props ?? {}), { maxWidth: BOX_W, maxLines: 4, max: 96, min: 48 });
  const top = areaTop(props ?? {});
  return (
    <Stage>
      <div style={{ position: "absolute", left: BOX_L, width: BOX_W, top, height: STAGE_H - top, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Strips lines={fit.lines} size={fit.size} seed="ph" />
      </div>
    </Stage>
  );
};
