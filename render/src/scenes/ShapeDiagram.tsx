import React from "react";
import { interpolate, spring, useCurrentFrame } from "remotion";
import { PaperCut, PaperShape, ShapeKind } from "../paper/PaperShape";
import { SUPPORT_AT } from "../paper/motion";
import { colors, fonts } from "../theme";
import { useAccent } from "./accent";
import { formatCount } from "./Counter";
import { list, num, str, strList } from "./coerce";
import { fitText, textWidth } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_L, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

type Mode = "circle" | "square" | "triangle" | "bar";

const modeOf = (value: unknown): Mode => {
  const key = str(value).toLowerCase();
  if (["square", "carre", "carré"].includes(key)) return "square";
  if (key === "triangle") return "triangle";
  if (["bar", "bars", "strip", "barre", "column"].includes(key)) return "bar";
  return "circle";
};

export const MIN_BAR = 22;

export const barHeights = (values: number[], maxH: number, minH = MIN_BAR): number[] => {
  const top = Math.max(0, ...values);
  return values.map((v) => (top > 0 ? Math.max(minH, (Math.max(0, v) / top) * maxH) : minH));
};

export const valueText = (value: number | null, unit: string): string => {
  if (value === null) return "";
  const places = Number.isInteger(value) ? 0 : Math.abs(value) < 10 ? 1 : 0;
  const n = formatCount(value, places);
  if (!unit) return n;
  return unit === "%" ? `${n} %` : `${n} ${unit}`;
};

const grow = (frame: number, at: number): number =>
  frame < at ? 0 : spring({ frame: frame - at, fps: 30, config: { damping: 15, stiffness: 90, mass: 0.9 } });

export const ShapeDiagram: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const mode = modeOf(props.shape);
  const raw = list(props.values, 8).map((v) => num(v));
  const values = raw.length > 0 ? raw.map((v) => Math.max(0, v ?? 0)) : [1];
  const unit = str(props.unit).slice(0, 8);
  const labels = strList(props.labels, 8);
  const n = values.length;
  const perShape = labels.length === n;
  const showValues = mode === "bar" || unit.length > 0;
  const top = areaTop(props);
  const slot0 = (mode === "bar" ? Math.min(BOX_W / n, 330) : BOX_W / n) - 16;
  const fitsIn = (width: number) => (l: string) => {
    const f = fitText(l, { maxWidth: width, maxLines: 2, max: 56, min: 30, prefer: true });
    return f.lines.every((line) => !line.includes("…") && textWidth(line, f.size) + f.size * 0.6 <= width);
  };
  const twoRows = perShape && n > 1 && !labels.every(fitsIn(slot0));
  const labelW = twoRows ? Math.min(BOX_W / 2, slot0 * 2 + 16) - 16 : slot0;
  const labelFits = perShape
    ? (() => {
        const fits = labels.map((l) => fitText(l, { maxWidth: labelW, maxLines: 2, max: 56, min: 30, prefer: true }));
        const size = Math.min(...fits.map((f) => f.size));
        return labels.map((l) => fitText(l, { maxWidth: labelW, maxLines: 2, max: size, min: Math.min(size, 30), prefer: true }));
      })()
    : [];
  const rowH = perShape ? Math.max(...labelFits.map((f) => stripsHeight(f.lines.length, f.size, 6))) : 0;
  const sharedFit = !perShape && labels.length > 0 ? fitText(labels.join(" · "), { maxWidth: BOX_W, maxLines: 2, max: 56, min: 38 }) : null;
  const labelH = perShape
    ? rowH * (twoRows ? 2 : 1) + (twoRows ? 12 : 0)
    : sharedFit
      ? stripsHeight(sharedFit.lines.length, sharedFit.size, 6)
      : 0;
  const valueTexts = values.map((_, i) => valueText(raw[i] ?? null, unit));
  const valueSize = Math.min(
    60,
    ...valueTexts.map((t) => (t ? Math.floor(((BOX_W / n - 12) / Math.max(1, textWidth(t, 100))) * 100) : 60)),
  );
  const valueH = showValues ? valueSize * 1.3 + 18 : 0;
  const baseGap = 34;
  const avail = STAGE_H - top - 40;
  const chartH = Math.min(mode === "bar" ? 600 : 420, avail - labelH - valueH - baseGap - 20);

  const slotW = mode === "bar" ? Math.min(BOX_W / n, 330) : BOX_W / n;
  const rowLeft = BOX_CX - (slotW * n) / 2;
  const top1 = Math.sqrt(Math.max(...values, 0.0001));
  const unitSize = Math.min(chartH, slotW - 18) / top1;
  const barW = Math.min(190, slotW * 0.62);
  const sizes = mode === "bar" ? values.map(() => barW) : values.map((v) => Math.max(18, unitSize * Math.sqrt(v)));
  const heights = mode === "bar" ? barHeights(values, chartH) : sizes;
  const placed = sizes.map((w, i) => {
    const cx = rowLeft + slotW * i + slotW / 2;
    return { x: cx - w / 2, w, h: heights[i], cx };
  });
  const labelCenters = placed.map((p) => p.cx);
  const drawnH = mode === "bar" ? chartH : Math.max(...heights);
  const blockH = valueH + drawnH + 14 + baseGap + labelH;
  const baseline = top + 20 + Math.max(0, (avail - blockH) / 2) + valueH + drawnH;
  const kind: ShapeKind = mode === "bar" ? "square" : mode;
  const baseIn = interpolate(frame, [-4, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: rowLeft - 20,
          top: baseline,
          width: (slotW * n + 40) * baseIn,
          height: 14,
        }}
      >
        <PaperCut kind="strip" color="ink" seed="sd-base" />
      </div>
      {placed.map((p, i) => {
        const at = enterFor(`values.${i}`, items, from, to);
        if (mode === "bar") {
          const g = grow(frame, at);
          const h = Math.max(0, p.h * g);
          const visible = frame >= at;
          const valueIn = interpolate(frame - at, [4, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <React.Fragment key={`bar-${i}`}>
              {visible ? (
                <div style={{ position: "absolute", left: p.x, top: baseline - h + 2, width: p.w, height: h }}>
                  <PaperCut kind="square" color={accent} seed={`sd-bar-${i}`} />
                </div>
              ) : null}
              {valueTexts[i] ? (
                <div
                  style={{
                    position: "absolute",
                    left: p.cx - slotW / 2,
                    width: slotW,
                    top: baseline - h - valueSize * 1.3 - 14,
                    textAlign: "center",
                    fontFamily: fonts.text,
                    fontWeight: 800,
                    fontSize: valueSize,
                    lineHeight: 1.3,
                    color: colors.ink,
                    whiteSpace: "nowrap",
                    opacity: valueIn,
                  }}
                >
                  {valueTexts[i]}
                </div>
              ) : null}
            </React.Fragment>
          );
        }
        return (
          <React.Fragment key={`shape-${i}`}>
            <PaperShape
              kind={kind}
              color={accent}
              size={p.w}
              x={p.x}
              y={baseline - p.h}
              enterAt={at}
              seed={`sd-${i}`}
              float={0}
              spin={0}
              origin="50% 100%"
              motion={{ dy: 0, spin: 0, from: 0.9 }}
            />
            {showValues && valueTexts[i] ? (
              <div
                style={{
                  position: "absolute",
                  left: p.cx - slotW / 2,
                  width: slotW,
                  top: baseline - p.h - valueSize * 1.3 - 14,
                  textAlign: "center",
                  fontFamily: fonts.text,
                  fontWeight: 800,
                  fontSize: valueSize,
                  lineHeight: 1.3,
                  color: colors.ink,
                  opacity: interpolate(frame - at, [4, 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                }}
              >
                {valueTexts[i]}
              </div>
            ) : null}
          </React.Fragment>
        );
      })}
      {perShape
        ? labelFits.map((fit, i) => (
            <div
              key={`label-${i}`}
              style={{
                position: "absolute",
                top: baseline + 14 + baseGap + (twoRows && i % 2 === 1 ? rowH + 12 : 0),
                left: labelCenters[i] - (labelW + 16) / 2,
                width: labelW + 16,
                display: "flex",
                justifyContent: "center",
              }}
            >
              <Strips
                lines={fit.lines}
                size={fit.size}
                enterAt={SUPPORT_AT + i * 2}
                seed={`sd-label-${i}`}
                gap={6}
                tilt={0}
              />
            </div>
          ))
        : sharedFit
          ? (
              <div style={{ position: "absolute", top: baseline + 14 + baseGap, left: BOX_L, width: BOX_W, display: "flex", justifyContent: "center" }}>
                <Strips lines={sharedFit.lines} size={sharedFit.size} enterAt={SUPPORT_AT} seed="sd-label" gap={6} />
              </div>
            )
          : null}
    </Stage>
  );
};
