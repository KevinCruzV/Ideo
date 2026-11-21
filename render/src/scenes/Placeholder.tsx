import React from "react";
import { AbsoluteFill } from "remotion";
import { PaperStrip } from "../paper/PaperStrip";
import type { SceneProps } from "./registry";

export const Placeholder: React.FC<SceneProps> = ({ segment }) => {
  const label = segment.type ? `${segment.kind} · ${segment.type}` : segment.kind;
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <PaperStrip text={label} color="cream" fontSize={84} rotate={-2} />
    </AbsoluteFill>
  );
};
