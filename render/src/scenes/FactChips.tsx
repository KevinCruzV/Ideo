import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { stripHeight } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { fitText, textWidth } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const DOT = 46;
const DOT_GAP = 28;
const PICTO = 260;

export const commonFit = (texts: string[], maxWidth: number, maxLines: number, max: number, min: number, prefer = false) => {
  const fits = texts.map((t) => fitText(t, { maxWidth, maxLines, max, min, prefer }));
  const size = Math.min(...fits.map((f) => f.size));
  return texts.map((t) => fitText(t, { maxWidth, maxLines, max: size, min: Math.min(size, min), prefer }));
};

export const FactChips: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const chips = strList(props.chips, 6);
  const shown = chips.length > 0 ? chips : ["…"];
  const hasPicto = pictoName(props.picto) !== null;
  const top = areaTop(props);
  const textW = BOX_W - DOT - DOT_GAP;
  const avail = STAGE_H - top - 20;
  const layoutFor = (max: number, picto: number) => {
    const fits = commonFit(shown, textW, 2, max, Math.min(44, max), true);
    const rowGap = shown.length <= 3 ? 44 : 30;
    const rowsH = fits.reduce((sum, f) => sum + stripsHeight(f.lines.length, f.size, 8), 0) + rowGap * (fits.length - 1);
    return { fits, rowGap, picto, total: rowsH + (picto ? picto + 50 : 0) };
  };
  let max = shown.length <= 3 ? 88 : shown.length <= 4 ? 76 : 62;
  let picto = hasPicto ? PICTO : 0;
  let plan = layoutFor(max, picto);
  while (plan.total > avail && (max > 44 || picto > 160)) {
    if (max > 60) max -= 4;
    else if (picto > 160) picto -= 30;
    else max -= 4;
    plan = layoutFor(max, picto);
  }
  const { fits, rowGap, total } = plan;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);
  const widest = Math.max(...fits.map((f) => Math.max(...f.lines.map((l) => textWidth(l, f.size) + f.size * 0.6), 0)));
  const blockW = Math.min(BOX_W, DOT + DOT_GAP + widest);
  const left = BOX_CX - blockW / 2;

  return (
    <Stage>
      {hasPicto ? <Picto name={props.picto} size={picto} x={BOX_CX - picto / 2} y={y0} rotate={-4} /> : null}
      <div
        style={{
          position: "absolute",
          left,
          top: y0 + (hasPicto ? picto + 50 : 0),
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          gap: rowGap,
        }}
      >
        {fits.map((fit, i) => {
          const at = enterFor(`chips.${i}`, items, from, to);
          const lineH = stripHeight(fit.size);
          return (
            <div key={`chip-${i}`} style={{ position: "relative", display: "flex", alignItems: "flex-start" }}>
              <div style={{ position: "relative", width: DOT, height: lineH, marginRight: DOT_GAP, flex: "none" }}>
                <PaperShape kind="circle" color={accent} size={DOT} y={(lineH - DOT) / 2} enterAt={i * 2 - 3} seed={`chip-dot-${i}`} float={1.5} />
              </div>
              <Strips lines={fit.lines} size={fit.size} enterAt={at} align="flex-start" seed={`chip-${i}`} gap={8} motion={{ dx: -40, dy: 0 }} />
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
