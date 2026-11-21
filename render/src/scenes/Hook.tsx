import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperStrip, stripHeight } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { useAccent } from "./accent";
import { Backdrop } from "./Backdrop";
import { str } from "./coerce";
import { fitText, splitKey } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";

const TEXT_W = BOX_W - 20;

export const Hook: React.FC<SceneProps> = ({ props, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 2, max: 92, min: 52 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 1, max: after ? 170 : 190, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 3, max: 84, min: 48 });
  const top = areaTop(props);
  const gap = 26;
  const blocks = [stripsHeight(head.lines.length, head.size), word.lines.length ? stripHeight(word.size) : 0, stripsHeight(tail.lines.length, tail.size)].filter(
    (h) => h > 0,
  );
  const textH = blocks.reduce((a, b) => a + b, 0) + gap * (blocks.length - 1);
  const textTop = top + (STAGE_H - top - textH) / 2;
  const duration = Math.max(1, to - from);
  const keyPulse = 1 + 0.03 * Math.sin((frame / 30) * 2.4) * Math.min(1, frame / 20);
  const lean = 2 * Math.sin((frame / duration) * Math.PI);

  return (
    <Stage>
      <Backdrop color={accent} size={820} cx={BOX_CX + 150} cy={textTop + textH / 2 - 30} seed="hook-disk" turn={12} />
      <Picto name={props.picto} size={230} x={BOX_L + BOX_W - 230} y={Math.max(top, textTop - 260)} rotate={8} enterAt={4} />
      <div
        style={{
          position: "absolute",
          left: BOX_L,
          width: BOX_W,
          top: textTop,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap,
          transform: `rotate(${lean * 0.3}deg)`,
        }}
      >
        <Strips lines={head.lines} size={head.size} enterAt={0} align="flex-start" seed="hook-head" tilt={-1} motion={{ dx: -60, dy: 0 }} />
        {word.lines.length > 0 ? (
          <PaperStrip
            text={word.lines[0]}
            color="ink"
            fontSize={word.size}
            enterAt={8}
            rotate={-2.5}
            seed="hook-key"
            float={4}
            motion={{ dx: 80, dy: 0, spin: 8 }}
            style={{ marginLeft: 20, scale: String(keyPulse) }}
          />
        ) : null}
        <Strips lines={tail.lines} size={tail.size} enterAt={14} align="flex-start" seed="hook-tail" motion={{ dx: -60, dy: 0 }} />
      </div>
    </Stage>
  );
};
