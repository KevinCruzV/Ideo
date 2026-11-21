import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const MARK = 160;

export const Quote: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const text = fitText(str(props.text, "…"), { maxWidth: BOX_W, maxLines: 6, max: 80, min: 44 });
  const speaker = fitText(str(props.speaker), { maxWidth: BOX_W - 100, maxLines: 1, max: 54, min: 40 });
  const textAt = enterFor("text", items, from, to);
  const top = areaTop(props);
  const textH = stripsHeight(text.lines.length, text.size, 10);
  const speakerH = speaker.lines.length ? stripsHeight(1, speaker.size) + 36 : 0;
  const total = MARK + 36 + textH + speakerH;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);

  return (
    <Stage>
      <PaperShape kind="square" color={accent} size={MARK} x={BOX_L + 6} y={y0} rotate={-8} seed="quote-mark" float={3}>
        <span style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: 180, lineHeight: 1, marginTop: 26, color: onPaper[accent] }}>«</span>
      </PaperShape>
      <Picto name={props.picto} size={200} x={BOX_L + BOX_W - 200} y={y0 - 30} rotate={6} enterAt={3} />
      <div
        style={{
          position: "absolute",
          left: BOX_L,
          width: BOX_W,
          top: y0 + MARK + 36,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: 36,
        }}
      >
        <Strips lines={text.lines} size={text.size} enterAt={textAt} stagger={3} align="flex-start" seed="quote-text" gap={10} motion={{ dx: -40, dy: 0 }} />
        {speaker.lines.length > 0 ? (
          <Strips
            lines={speaker.lines}
            size={speaker.size}
            color="ink"
            enterAt={items.some((i) => i.el === "speaker") ? enterFor("speaker", items, from, to) : textAt + 10}
            align="flex-end"
            seed="quote-speaker"
            style={{ alignSelf: "flex-end" }}
          />
        ) : null}
      </div>
    </Stage>
  );
};
