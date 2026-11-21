import React from "react";
import { useCurrentFrame } from "remotion";
import { fonts, onPaper, PaperColor, colors, shadowFilter, stripClip } from "../theme";
import { enterScale, jitter } from "./stopMotion";

export type PaperStripProps = {
  text: string;
  color?: PaperColor;
  enterAt?: number;
  fontSize?: number;
  rotate?: number;
  seed?: string;
  style?: React.CSSProperties;
};

export const PaperStrip: React.FC<PaperStripProps> = ({
  text,
  color = "cream",
  enterAt = 0,
  fontSize = 64,
  rotate = -2,
  seed,
  style,
}) => {
  const frame = useCurrentFrame();
  const scale = enterScale(frame, enterAt);
  const angle = rotate + jitter(seed ?? text, frame, 0.8);

  return (
    <div
      style={{
        display: "inline-block",
        opacity: scale === 0 ? 0 : 1,
        transform: `rotate(${angle}deg) scale(${scale})`,
        filter: shadowFilter,
        ...style,
      }}
    >
      <div
        style={{
          background: colors[color],
          color: onPaper[color],
          fontFamily: fonts.text,
          fontWeight: 800,
          fontSize,
          lineHeight: 1.15,
          padding: `${fontSize * 0.1}px ${fontSize * 0.3}px`,
          clipPath: stripClip,
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </div>
    </div>
  );
};
