import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { hasVisual, Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { strList } from "./coerce";
import { commonFit } from "./FactChips";
import { areaFor, FitBox, largestFitting } from "./FitBox";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";
import { useBeat } from "./beats";

const PICTO = 240;
const BADGE_GAP = 30;

export const StackList: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const beat = useBeat();
  const entries = strList(props.items, 5);
  const shown = entries.length > 0 ? entries : ["…"];
  const hasPicto = hasVisual(props.picto);
  const dense = shown.join(" ").length > 120;
  const badge = dense ? 62 : shown.length <= 3 ? 104 : 80;
  const badgeGap = dense ? 18 : BADGE_GAP;
  const rowGap = shown.length <= 3 ? 46 : 22;
  const area = areaFor(areaTop(props) + 10, BOX_L, BOX_W);
  const picto = hasPicto ? (dense ? 130 : PICTO) : 0;
  const fitAt = (max: number) => commonFit(shown, BOX_W - badge - badgeGap, 3, max, Math.min(44, max));
  const heightAt = (max: number) =>
    (picto ? picto + 40 : 0) + fitAt(max).reduce((sum, f) => sum + Math.max(badge, stripsHeight(f.lines.length, f.size, 8)), 0) + rowGap * (shown.length - 1);
  const max = largestFitting(shown.length <= 3 ? 96 : 80, 44, (m) => heightAt(m) <= area.height);
  const fits = fitAt(max);

  return (
    <Stage>
      <FitBox area={area} maxScale={1.2}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40 }}>
          {hasPicto ? <Picto name={props.picto} size={picto} rotate={5} /> : null}
          <div style={{ display: "flex", flexDirection: "column", gap: rowGap }}>
            {fits.map((fit, i) => {
              const at = enterFor(`items.${i}`, items, from, to);
              return (
                <div key={`stack-${i}`} style={{ display: "flex", alignItems: "center", gap: badgeGap, minHeight: badge, transform: beat && beat.index % fits.length === i ? `translateX(${46 * beat.wave}px) scale(${1 + 0.08 * beat.wave}) rotate(${-1.5 * beat.wave}deg)` : undefined, transformOrigin: "0 50%" }}>
                  <div style={{ position: "relative", width: badge, height: badge, flex: "none" }}>
                    <PaperShape kind="square" color={accent} size={badge} rotate={i % 2 === 0 ? -5 : 4} enterAt={i * 2 - 3} seed={`stack-badge-${i}`} float={2}>
                      <span style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: badge * 0.6, lineHeight: 1, color: onPaper[accent] }}>{i + 1}</span>
                    </PaperShape>
                  </div>
                  <Strips lines={fit.lines} size={fit.size} enterAt={at} align="flex-start" seed={`stack-${i}`} gap={8} motion={{ dx: -40, dy: 0 }} />
                </div>
              );
            })}
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
