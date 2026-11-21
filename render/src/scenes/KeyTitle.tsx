import React from "react";
import { PaperStrip, stripHeight } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { fitText, splitKey } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const TEXT_W = BOX_W;
const PICTO = 300;

export const KeyTitle: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 3, max: 100, min: 52 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 2, max: 176, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 3, max: 100, min: 52 });
  const textAt = Math.min(enterFor("text", items, from, to), enterFor("accent", items, from, to));
  const accentAt = textAt + 5;
  const hasPicto = pictoName(props.picto) !== null;
  const gap = 24;
  const blocks = [
    hasPicto ? PICTO : 0,
    stripsHeight(head.lines.length, head.size),
    word.lines.length ? word.lines.length * stripHeight(word.size) + (word.lines.length - 1) * 12 : 0,
    stripsHeight(tail.lines.length, tail.size),
  ].filter((h) => h > 0);
  const total = blocks.reduce((a, b) => a + b, 0) + gap * (blocks.length - 1) + (hasPicto ? 20 : 0);
  const top = areaTop(props);
  const startY = top + Math.max(0, (STAGE_H - top - total) / 2);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: BOX_CX - TEXT_W / 2,
          width: TEXT_W,
          top: startY,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap,
        }}
      >
        {hasPicto ? <Picto name={props.picto} size={PICTO} rotate={-5} style={{ marginBottom: 20 }} /> : null}
        <Strips lines={head.lines} size={head.size} enterAt={textAt} seed="kt-head" />
        {word.lines.length > 0 ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            {word.lines.map((line, i) => (
              <PaperStrip
                key={`kt-key-${i}`}
                text={line}
                color={accent}
                fontSize={word.size}
                enterAt={accentAt + i * 3}
                rotate={i % 2 === 0 ? -2.5 : 1.5}
                seed={`kt-key-${i}`}
                float={3.5}
                motion={{ dy: 0, dx: i % 2 === 0 ? -90 : 90, spin: -8 }}
              />
            ))}
          </div>
        ) : null}
        <Strips lines={tail.lines} size={tail.size} enterAt={accentAt + 4} seed="kt-tail" />
      </div>
    </Stage>
  );
};
