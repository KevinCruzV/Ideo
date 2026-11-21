import React from "react";
import { SUPPORT_AT } from "../paper/motion";
import { PaperStrip } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import { fitText, splitKey } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const TEXT_W = BOX_W;
const PICTO = 300;

export const KeyTitle: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 4, max: 100, min: 56 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 2, max: 176, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 4, max: 100, min: 56 });
  const textAt = Math.min(enterFor("text", items, from, to), enterFor("accent", items, from, to));
  const accentAt = textAt + 5;
  const hasPicto = pictoName(props.picto) !== null;

  return (
    <Stage>
      <FitBox area={areaFor(areaTop(props) + 10, BOX_L, BOX_W)} maxScale={1.1}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24, width: TEXT_W }}>
          {hasPicto ? <Picto name={props.picto} size={PICTO} rotate={-5} style={{ marginBottom: 12 }} /> : null}
          <Strips lines={head.lines} size={head.size} enterAt={Math.min(textAt, SUPPORT_AT)} seed="kt-head" />
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
      </FitBox>
    </Stage>
  );
};
