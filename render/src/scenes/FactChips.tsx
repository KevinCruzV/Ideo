import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { stripHeight } from "../paper/PaperStrip";
import { hasVisual, Picto } from "../pictos/Picto";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { areaFor, FitBox, largestFitting } from "./FitBox";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";
import { useBeat } from "./beats";

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
  const beat = useBeat();
  const chips = strList(props.chips, 6);
  const shown = chips.length > 0 ? chips : ["…"];
  const hasPicto = hasVisual(props.picto);
  const textW = BOX_W - DOT - DOT_GAP;
  const rowGap = shown.length <= 3 ? 44 : 28;
  const area = areaFor(areaTop(props) + 10, BOX_L, BOX_W);
  const picto = hasPicto ? (shown.length > 4 ? 170 : PICTO) : 0;
  const fitAt = (max: number) => commonFit(shown, textW, 2, max, Math.min(44, max), true);
  const heightAt = (max: number) =>
    (picto ? picto + 40 : 0) + fitAt(max).reduce((sum, f) => sum + stripsHeight(f.lines.length, f.size, 8), 0) + rowGap * (shown.length - 1);
  const max = largestFitting(shown.length <= 3 ? 104 : shown.length <= 4 ? 88 : 76, 44, (m) => heightAt(m) <= area.height);
  const fits = fitAt(max);

  return (
    <Stage>
      <FitBox area={area} maxScale={1.25}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40 }}>
          {hasPicto ? <Picto name={props.picto} size={picto} rotate={-4} /> : null}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: rowGap }}>
            {fits.map((fit, i) => {
              const at = enterFor(`chips.${i}`, items, from, to);
              const lineH = stripHeight(fit.size);
              return (
                <div key={`chip-${i}`} style={{ position: "relative", display: "flex", alignItems: "flex-start", transform: beat && beat.index % fits.length === i ? `translateX(${46 * beat.wave}px) scale(${1 + 0.08 * beat.wave}) rotate(${-1.5 * beat.wave}deg)` : undefined, transformOrigin: "0 50%" }}>
                  <div style={{ position: "relative", width: DOT, height: lineH, marginRight: DOT_GAP, flex: "none" }}>
                    <PaperShape kind="circle" color={accent} size={DOT} y={(lineH - DOT) / 2} enterAt={i * 2 - 3} seed={`chip-dot-${i}`} float={1.5} />
                  </div>
                  <Strips lines={fit.lines} size={fit.size} enterAt={at} align="flex-start" seed={`chip-${i}`} gap={8} motion={{ dx: -40, dy: 0 }} />
                </div>
              );
            })}
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
