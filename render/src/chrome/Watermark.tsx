import React from "react";
import { useCurrentFrame } from "remotion";
import { colors, fonts, layout, shadowFilter } from "../theme";
import { jitter } from "../paper/stopMotion";

export const Watermark: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: "absolute",
        top: layout.marginTop,
        right: layout.marginSide,
        transform: `rotate(${3 + jitter("watermark", frame, 0.6)}deg)`,
        filter: shadowFilter,
      }}
    >
      <div
        style={{
          background: colors.cream,
          color: colors.ink,
          fontFamily: fonts.brand,
          fontWeight: 800,
          fontSize: 36,
          lineHeight: 1,
          padding: "12px 24px",
        }}
      >
        {text}
      </div>
    </div>
  );
};
