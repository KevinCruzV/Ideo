import React from "react";
import { useCurrentFrame } from "remotion";
import { PaperStrip } from "../paper/PaperStrip";
import { useAccent } from "./accent";
import { Backdrop } from "./Backdrop";
import { str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import { fitText, splitKey } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips } from "./Strips";

const TEXT_W = BOX_W - 20;

export const Hook: React.FC<SceneProps> = ({ props, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const text = str(props.text, "…");
  const { before, key, after } = splitKey(text, str(props.accent) || undefined);
  const head = fitText(before, { maxWidth: TEXT_W, maxLines: 3, max: 92, min: 56 });
  const word = fitText(key, { maxWidth: TEXT_W, maxLines: 1, max: after ? 170 : 190, min: 64 });
  const tail = fitText(after, { maxWidth: TEXT_W, maxLines: 4, max: 84, min: 56 });
  const top = areaTop(props);
  const duration = Math.max(1, to - from);
  const keyPulse = 1 + 0.035 * Math.sin((frame / 30) * 2.4) * Math.min(1, frame / 20);
  const lean = 2 * Math.sin((frame / duration) * Math.PI);

  return (
    <Stage>
      <Backdrop color={accent} size={820} cx={BOX_CX + 150} cy={top + (STAGE_H - top) / 2 - 30} seed="hook-disk" turn={12} />
      <FitBox area={areaFor(top + 10, BOX_L, BOX_W)}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 26, width: TEXT_W, transform: `rotate(${lean * 0.3}deg)` }}>
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
      </FitBox>
    </Stage>
  );
};
