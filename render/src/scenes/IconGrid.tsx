import React from "react";
import { PaperShape, ShapeKind } from "../paper/PaperShape";
import { SUPPORT_AT } from "../paper/motion";
import { hasVisual, Picto } from "../pictos/Picto";
import { useAccent } from "./accent";
import { list, str } from "./coerce";
import { commonFit } from "./FactChips";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { areaFor, FitBox } from "./FitBox";
import { fonts, onPaper } from "../theme";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const ALIASES: Record<string, ShapeKind> = {
  circle: "circle",
  rond: "circle",
  cercle: "circle",
  dot: "circle",
  square: "square",
  carre: "square",
  carré: "square",
  box: "square",
  triangle: "triangle",
  diamond: "diamond",
  losange: "diamond",
  arrow: "arrow",
  fleche: "arrow",
  flèche: "arrow",
  strip: "strip",
  bande: "strip",
  bar: "strip",
  line: "strip",
};

const ORDER: ShapeKind[] = ["circle", "square", "triangle", "diamond"];

export const shapeKind = (value: unknown, index: number): ShapeKind =>
  ALIASES[str(value).toLowerCase()] ?? ORDER[index % ORDER.length];

export const cellMark = (label: string, index: number): string => {
  const letter = label.match(/\p{L}|\p{N}/u);
  return letter ? letter[0].toUpperCase() : String(index + 1);
};

export const IconGrid: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const cells = list(props.cells, 9).map((c) => {
    const o = c && typeof c === "object" ? (c as Record<string, unknown>) : { label: c };
    return { picto: hasVisual(o.picto) ? (o.picto as string) : null, label: str(o.label) };
  });
  const shown = cells.length > 0 ? cells : [{ picto: null, label: "" }];
  const cols = shown.length <= 4 ? 2 : 3;
  const top = areaTop(props);
  const cellW = BOX_W / cols;
  const fits = commonFit(
    shown.map((c) => c.label),
    cellW - 24,
    3,
    cols === 2 ? 64 : 52,
    cols === 2 ? 44 : 36,
    true,
  );
  const labelH = Math.max(0, ...fits.map((f) => stripsHeight(f.lines.length, f.size, 6)));
  const art = cols === 2 ? 280 : shown.length > 6 ? 170 : 210;
  const rowGap = cols === 2 ? 56 : 40;

  return (
    <Stage>
      <FitBox area={areaFor(top + 10, BOX_L, BOX_W)} maxScale={1.25}>
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, ${cellW}px)`, rowGap }}>
          {shown.map((cell, i) => {
            const at = i === 0 ? Math.min(SUPPORT_AT, enterFor("cells.0", items, from, to)) : enterFor(`cells.${i}`, items, from, to);
            const fit = fits[i];
            const disc = art * 0.84;
            return (
              <div key={`cell-${i}`} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
                <div style={{ position: "relative", width: art, height: art }}>
                  {cell.picto ? (
                    <Picto name={cell.picto} size={art} enterAt={at} rotate={i % 2 ? 4 : -4} seed={`cell-picto-${i}`} />
                  ) : (
                    <PaperShape kind="circle" color={accent} size={disc} x={(art - disc) / 2} y={(art - disc) / 2} rotate={i % 2 ? 4 : -4} enterAt={at} seed={`cell-${i}`}>
                      <span style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: disc * 0.52, lineHeight: 1, color: onPaper[accent], marginTop: disc * 0.04 }}>
                        {cellMark(cell.label, i)}
                      </span>
                    </PaperShape>
                  )}
                </div>
                <div style={{ height: labelH, display: "flex", alignItems: "flex-start" }}>
                  <Strips lines={fit.lines} size={fit.size} enterAt={at + 3} seed={`cell-label-${i}`} gap={6} />
                </div>
              </div>
            );
          })}
        </div>
      </FitBox>
    </Stage>
  );
};
