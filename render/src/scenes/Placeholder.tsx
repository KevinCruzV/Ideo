import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H, STAGE_W } from "./Stage";
import { Strips } from "./Strips";

const firstText = (props: Record<string, unknown>): string => {
  const preferred = str(props.text) || str(props.label) || str(props.title);
  if (preferred) return preferred;
  for (const value of Object.values(props)) {
    const s = str(value);
    if (s) return s;
  }
  return "";
};

export const Placeholder: React.FC<SceneProps> = ({ props }) => {
  const accent = useAccent();
  const fit = fitText(firstText(props ?? {}), { maxWidth: 900, maxLines: 4, max: 96, min: 48 });
  return (
    <Stage>
      <PaperShape kind="circle" color={accent} size={260} x={STAGE_W - 320} y={60} seed="ph-circle" />
      <div style={{ position: "absolute", left: 60, right: 60, top: 0, height: STAGE_H, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Strips lines={fit.lines} size={fit.size} seed="ph" />
      </div>
    </Stage>
  );
};
