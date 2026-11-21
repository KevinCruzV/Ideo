import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

export const Quote: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const text = fitText(str(props.text, "…"), { maxWidth: 920, maxLines: 6, max: 84, min: 46 });
  const speaker = fitText(str(props.speaker), { maxWidth: 760, maxLines: 1, max: 56, min: 40 });
  const textAt = enterFor("text", items, from, to);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: 56,
          right: 56,
          top: 0,
          bottom: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          gap: 40,
        }}
      >
        <div style={{ position: "relative", width: 170, height: 170, marginLeft: 8 }}>
          <PaperShape kind="square" color={accent} size={170} rotate={-8} seed="quote-mark">
            <span
              style={{
                fontFamily: fonts.text,
                fontWeight: 800,
                fontSize: 190,
                lineHeight: 1,
                marginTop: 30,
                color: onPaper[accent],
              }}
            >
              «
            </span>
          </PaperShape>
        </div>
        <Strips lines={text.lines} size={text.size} enterAt={textAt} stagger={2} align="flex-start" seed="quote-text" gap={12} />
        {speaker.lines.length > 0 ? (
          <Strips
            lines={speaker.lines}
            size={speaker.size}
            color="ink"
            enterAt={items.some((i) => i.el === "speaker") ? enterFor("speaker", items, from, to) : textAt + 8}
            align="flex-end"
            seed="quote-speaker"
            style={{ alignSelf: "flex-end" }}
          />
        ) : null}
      </div>
    </Stage>
  );
};
