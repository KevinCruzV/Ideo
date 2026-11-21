import React from "react";
import { PaperShape, ShapeKind } from "../paper/PaperShape";
import { useAccent } from "./accent";
import { list, str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_H, STAGE_W } from "./Stage";
import { Strips } from "./Strips";
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

const TILTS = [-6, 5, -3, 8, -8, 3, 6, -4, 2];

export const IconGrid: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const cells = list(props.cells, 9).map((c, i) => {
    const o = c && typeof c === "object" ? (c as Record<string, unknown>) : { label: c };
    return { kind: shapeKind(o.shape, i), label: str(o.label) };
  });
  const shown = cells.length > 0 ? cells : [{ kind: "circle" as ShapeKind, label: "" }];
  const cols = shown.length <= 4 ? 2 : 3;
  const rows = Math.ceil(shown.length / cols);
  const cellW = (STAGE_W - 96) / cols;
  const cellH = Math.min(STAGE_H / rows, 520);
  const shape = Math.min(cellW * 0.6, cellH * 0.55, 240);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: 48,
          right: 48,
          top: (STAGE_H - cellH * rows) / 2,
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, ${cellW}px)`,
          gridAutoRows: `${cellH}px`,
        }}
      >
        {shown.map((cell, i) => {
          const at = enterFor(`cells.${i}`, items, from, to);
          const wide = cell.kind === "strip" || cell.kind === "arrow";
          const size = wide ? shape * 0.42 : shape;
          const w = wide ? size * 2.4 : size;
          const h = cell.kind === "strip" ? size * 0.5 : wide ? size * 0.9 : size;
          const fit = fitText(cell.label, { maxWidth: cellW - 24, maxLines: 2, max: cols === 2 ? 60 : 50, min: 40 });
          return (
            <div
              key={`cell-${i}`}
              style={{ position: "relative", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}
            >
              <div style={{ position: "relative", width: w, height: shape }}>
                <PaperShape
                  kind={cell.kind}
                  color={accent}
                  size={size}
                  y={(shape - h) / 2}
                  rotate={TILTS[i % TILTS.length]}
                  enterAt={at}
                  seed={`cell-${i}`}
                />
              </div>
              <Strips lines={fit.lines} size={fit.size} enterAt={at + 2} seed={`cell-label-${i}`} gap={6} style={{ marginTop: 26 }} />
            </div>
          );
        })}
      </div>
    </Stage>
  );
};
