import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { PaperStrip } from "../paper/PaperStrip";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText, splitKey } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const TEXT_W = 920;

export const KeyTitle: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 3, max: 96, min: 52 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 2, max: 170, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 3, max: 96, min: 52 });
  const textAt = enterFor("text", items, from, to);
  const accentAt = Math.max(textAt + 4, enterFor("accent", items, from, to));

  return (
    <Stage>
      <PaperShape kind="square" color={accent} size={170} x={820} y={70} rotate={12} seed="kt-square" />
      <PaperShape kind="circle" color="cream" size={300} x={60} y={STAGE_H - 330} seed="kt-circle" />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 24,
        }}
      >
        <Strips lines={head.lines} size={head.size} enterAt={textAt} seed="kt-head" />
        {word.lines.map((line, i) => (
          <PaperStrip
            key={`kt-key-${i}`}
            text={line}
            color={accent}
            fontSize={word.size}
            enterAt={accentAt + i * 3}
            rotate={i % 2 === 0 ? -2.5 : 1.5}
            seed={`kt-key-${i}`}
          />
        ))}
        <Strips lines={tail.lines} size={tail.size} enterAt={textAt + 2} seed="kt-tail" />
      </div>
    </Stage>
  );
};
