import React from "react";
import { AbsoluteFill } from "remotion";
import grainUrl from "../../public/grain.png";
import { colors } from "../theme";

export const Background: React.FC = () => (
  <AbsoluteFill style={{ background: colors.background }}>
    <AbsoluteFill
      style={{
        backgroundImage: `url(${grainUrl})`,
        backgroundSize: "384px 384px",
        backgroundRepeat: "repeat",
        mixBlendMode: "multiply",
        opacity: 0.9,
      }}
    />
  </AbsoluteFill>
);
