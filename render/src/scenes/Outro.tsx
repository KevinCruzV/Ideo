import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { PaperStrip } from "../paper/PaperStrip";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "./fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";

const TEXT_W = 900;

export const Outro: React.FC<SceneProps> = ({ props }) => {
  const accent = useAccent();
  const text = str(props.text, "À suivre");
  const cut = text.indexOf(":");
  const head = cut > 0 ? text.slice(0, cut).trim() : text;
  const tail = cut > 0 ? text.slice(cut + 1).trim() : "";
  const headFit = fitText(head, { maxWidth: TEXT_W, maxLines: 3, max: 84, min: 52 });
  const tailFit = fitText(tail, { maxWidth: TEXT_W, maxLines: 2, max: 130, min: 60 });

  return (
    <Stage>
      <PaperShape kind="circle" color="cream" size={420} x={-120} y={STAGE_H - 470} seed="outro-circle" />
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          top: 120,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 26,
        }}
      >
        <Strips lines={headFit.lines} size={headFit.size} enterAt={2} align="flex-start" seed="outro-head" />
        {tailFit.lines.map((line, i) => (
          <PaperStrip
            key={line}
            text={line}
            color={accent}
            fontSize={tailFit.size}
            enterAt={8 + i * 3}
            rotate={i % 2 === 0 ? 2 : -1.5}
            seed={`outro-tail-${i}`}
            style={{ marginLeft: 30 }}
          />
        ))}
      </div>
      <PaperShape kind="arrow" color={accent} size={190} x={480} y={STAGE_H - 230} rotate={-6} enterAt={14} seed="outro-arrow" />
    </Stage>
  );
};
