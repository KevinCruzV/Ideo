import React from "react";
import { PaperShape, ShapeKind } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { pictoName } from "../pictos/library";
import { useAccent } from "./accent";
import { list, str } from "./coerce";
import { commonFit } from "./FactChips";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
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

export const IconGrid: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const cells = list(props.cells, 9).map((c, i) => {
    const o = c && typeof c === "object" ? (c as Record<string, unknown>) : { label: c };
    return { kind: shapeKind(o.shape, i), picto: pictoName(o.picto), label: str(o.label) };
  });
  const shown = cells.length > 0 ? cells : [{ kind: "circle" as ShapeKind, picto: null, label: "" }];
  const cols = shown.length <= 4 ? 2 : 3;
  const rows = Math.ceil(shown.length / cols);
  const top = areaTop(props);
  const cellW = BOX_W / cols;
  const fits = commonFit(
    shown.map((c) => c.label),
    cellW - 24,
    2,
    cols === 2 ? 60 : 48,
    34,
    true,
  );
  const labelH = Math.max(0, ...fits.map((f) => stripsHeight(f.lines.length, f.size, 6)));
  const avail = STAGE_H - top;
  const cellH = Math.min(avail / rows, cols === 2 ? 470 : 360);
  const art = Math.max(110, Math.min(cellW * 0.66, cellH - labelH - 34, cols === 2 ? 270 : 210));
  const gridTop = top + (avail - cellH * rows) / 2;

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: BOX_L,
          top: gridTop,
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, ${cellW}px)`,
          gridAutoRows: `${cellH}px`,
        }}
      >
        {shown.map((cell, i) => {
          const at = enterFor(`cells.${i}`, items, from, to);
          const wide = cell.kind === "strip" || cell.kind === "arrow";
          const size = wide ? art * 0.42 : art * 0.86;
          const w = wide ? size * 2.4 : size;
          const h = cell.kind === "strip" ? size * 0.5 : wide ? size * 0.9 : size;
          const fit = fits[i];
          return (
            <div key={`cell-${i}`} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 24 }}>
              <div style={{ position: "relative", width: art, height: art }}>
                {cell.picto ? (
                  <Picto name={cell.picto} size={art} enterAt={at} rotate={i % 2 ? 4 : -4} seed={`cell-picto-${i}`} />
                ) : (
                  <PaperShape kind={cell.kind} color={accent} size={size} w={w} h={h} x={(art - w) / 2} y={(art - h) / 2} rotate={i % 2 ? 4 : -4} enterAt={at} seed={`cell-${i}`} />
                )}
              </div>
              <div style={{ height: labelH, display: "flex", alignItems: "flex-start" }}>
                <Strips lines={fit.lines} size={fit.size} enterAt={at + 3} seed={`cell-label-${i}`} gap={6} />
              </div>
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
