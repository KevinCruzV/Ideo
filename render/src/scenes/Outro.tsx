import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { PaperStrip } from "../paper/PaperStrip";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";

const TEXT_W = 900;

export const splitOutro = (text: string): { head: string; tail: string } => {
  const cut = text.indexOf(":");
  if (cut > 0) return { head: text.slice(0, cut).trim(), tail: text.slice(cut + 1).trim() };
  const words = text.split(" ").filter((w) => w.length > 0);
  if (words.length < 4) return { head: text, tail: "" };
  return { head: words.slice(0, -2).join(" "), tail: words.slice(-2).join(" ") };
};

export const Outro: React.FC<SceneProps> = ({ props }) => {
  const accent = useAccent();
  const text = str(props.text, "À suivre");
  const { head, tail } = splitOutro(text);
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
