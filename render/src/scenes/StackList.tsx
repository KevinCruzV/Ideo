import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { stripHeight } from "../paper/PaperStrip";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { commonFit } from "./FactChips";
import { textWidth } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const PICTO = 240;
const BADGE_GAP = 30;

export const StackList: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const entries = strList(props.items, 5);
  const shown = entries.length > 0 ? entries : ["…"];
  const hasPicto = pictoName(props.picto) !== null;
  const top = areaTop(props);
  const avail = STAGE_H - top - 20;
  const layoutFor = (max: number, picto: number) => {
    const badge = Math.min(shown.length <= 3 ? 104 : 88, Math.round(max * 1.4));
    const fits = commonFit(shown, BOX_W - badge - BADGE_GAP, 2, max, Math.min(44, max));
    const rowGap = shown.length <= 3 ? 46 : 30;
    const rowH = fits.map((f) => Math.max(badge, stripsHeight(f.lines.length, f.size, 8)));
    const rowsH = rowH.reduce((a, b) => a + b, 0) + rowGap * (fits.length - 1);
    return { badge, fits, rowGap, rowH, picto, total: rowsH + (picto ? picto + 50 : 0) };
  };
  let max = shown.length <= 3 ? 80 : 66;
  let picto = hasPicto ? PICTO : 0;
  let plan = layoutFor(max, picto);
  while (plan.total > avail && (max > 44 || picto > 150)) {
    if (max > 60) max -= 4;
    else if (picto > 150) picto -= 30;
    else max -= 4;
    plan = layoutFor(max, picto);
  }
  const { badge, fits, rowGap, rowH, total } = plan;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);
  const widest = Math.max(...fits.map((f) => Math.max(...f.lines.map((l) => textWidth(l, f.size) + f.size * 0.6), 0)));
  const blockW = Math.min(BOX_W, badge + BADGE_GAP + widest);

  return (
    <Stage>
      {hasPicto ? <Picto name={props.picto} size={picto} x={BOX_CX - picto / 2} y={y0} rotate={5} /> : null}
      <div
        style={{
          position: "absolute",
          left: BOX_CX - blockW / 2,
          top: y0 + (hasPicto ? picto + 50 : 0),
          display: "flex",
          flexDirection: "column",
          gap: rowGap,
        }}
      >
        {fits.map((fit, i) => {
          const at = enterFor(`items.${i}`, items, from, to);
          const textH = stripsHeight(fit.lines.length, fit.size, 8);
          return (
            <div key={`stack-${i}`} style={{ display: "flex", alignItems: "center", gap: BADGE_GAP, minHeight: rowH[i] }}>
              <div style={{ position: "relative", width: badge, height: badge, flex: "none" }}>
                <PaperShape kind="square" color={accent} size={badge} rotate={i % 2 === 0 ? -5 : 4} enterAt={i * 2 - 3} seed={`stack-badge-${i}`} float={2}>
                  <span style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: badge * 0.6, lineHeight: 1, color: onPaper[accent] }}>{i + 1}</span>
                </PaperShape>
              </div>
              <div style={{ height: textH, display: "flex", alignItems: "center", minWidth: stripHeight(fit.size) }}>
                <Strips lines={fit.lines} size={fit.size} enterAt={at} align="flex-start" seed={`stack-${i}`} gap={8} motion={{ dx: -40, dy: 0 }} />
              </div>
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
