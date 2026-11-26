import React from "react";
import { SUPPORT_AT } from "../paper/motion";
import { PaperStrip } from "../paper/PaperStrip";
import { hasVisual, Picto } from "../pictos/Picto";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import { fitText, splitKey, textWidth } from "../text/fit";
import { useCurrentFrame } from "remotion";
import { PaperCut } from "../paper/PaperShape";
import { useBeat, useBeats } from "./beats";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { BRAND_WIDE, fonts } from "../theme";
import { enterFor } from "./timing";

const TEXT_W = BOX_W;
const PICTO = 300;

export const KeyTitle: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const frame = useCurrentFrame();
  const beats = useBeats();
  const beat = useBeat();
  const evenBeats = beats.filter((b, i) => i % 2 === 0 && b <= frame);
  const lastEven = evenBeats.length ? evenBeats[evenBeats.length - 1] : null;
  const underline = lastEven === null ? 0 : 1 - Math.pow(1 - Math.min(1, (frame - lastEven) / 10), 3);
  const keyPop = beat && beat.index % 2 === 1 ? beat.wave : 0;
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 4, max: 100, min: 56 });
  const word = fitText(key, { maxWidth: TEXT_W / BRAND_WIDE, maxLines: 2, max: 176, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 4, max: 100, min: 56 });
  const textAt = Math.min(enterFor("text", items, from, to), enterFor("accent", items, from, to));
  const accentAt = textAt + 5;
  const hasPicto = hasVisual(props.picto);
  const underlineW = Math.max(0, ...word.lines.map((l) => textWidth(l, word.size) * BRAND_WIDE + word.size * 0.6)) * 0.9;

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
                  family={fonts.brand}
                  weight={900}
                  enterAt={accentAt + i * 3}
                  rotate={i % 2 === 0 ? -2.5 : 1.5}
                  seed={`kt-key-${i}`}
                  float={3.5}
                  motion={{ dy: 0, dx: i % 2 === 0 ? -90 : 90, spin: -8 }}
                  style={{ scale: String(1 + 0.08 * keyPop) }}
                />
              ))}
              {underline > 0 ? (
                <div style={{ width: underlineW, height: 22, marginTop: -2, transform: `rotate(-1.5deg) scaleX(${underline})`, transformOrigin: "0 50%" }}>
                  <div style={{ position: "relative", width: "100%", height: "100%" }}>
                    <PaperCut kind="strip" color="ink" seed="kt-underline" />
                  </div>
                </div>
              ) : (
                <div style={{ height: 20 }} />
              )}
            </div>
          ) : null}
          <Strips lines={tail.lines} size={tail.size} enterAt={accentAt + 4} seed="kt-tail" />
        </div>
      </FitBox>
    </Stage>
  );
};
