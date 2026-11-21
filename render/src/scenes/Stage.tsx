import React from "react";
import { layout } from "../theme";

export const STAGE_W = layout.width;
export const STAGE_H = layout.stageBottom - layout.stageTop;

export const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      top: layout.stageTop,
      width: STAGE_W,
      height: STAGE_H,
      overflow: "hidden",
    }}
  >
    {children}
  </div>
);
