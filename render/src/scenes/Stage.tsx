import React from "react";
import { content, layout } from "../theme";

export const STAGE_W = layout.width;
export const STAGE_H = layout.stageBottom - layout.stageTop;
export const BOX_L = content.left;
export const BOX_R = content.right;
export const BOX_W = content.width;
export const BOX_CX = content.center;
export const KICKER_SPACE = 96;

export const areaTop = (props: Record<string, unknown>): number =>
  typeof props.kicker === "string" && props.kicker.trim().length > 0 ? KICKER_SPACE : 0;

export const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      top: layout.stageTop,
      width: STAGE_W,
      height: STAGE_H,
    }}
  >
    {children}
  </div>
);
