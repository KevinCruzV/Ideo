import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { stripHeight } from "../paper/PaperStrip";
import { hasVisual, Picto } from "../pictos/Picto";
import { useAccent } from "./accent";
import { list, str } from "./coerce";
import { areaFor, FitBox, largestFitting } from "./FitBox";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";
import { useBeat } from "./beats";

const RAIL = 150;
const LABEL_W = BOX_W - RAIL - 10;

type Mark = { at: string; label: string };

const Rail: React.FC<{ height: number; children: React.ReactNode }> = ({ height, children }) => (
  <div style={{ position: "relative", width: RAIL, height, flex: "none", display: "flex", alignItems: "center", justifyContent: "center" }}>{children}</div>
);

export const Timeline: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const beat = useBeat();
  const marks: Mark[] = list(props.marks, 5).map((m) => {
    const o = m && typeof m === "object" ? (m as Record<string, unknown>) : { label: m };
    const at = str(o.at);
    return { at, label: str(o.label) || at };
  });
  const hasPicto = hasVisual(props.picto);
  const few = marks.length <= 3;
  const capH = hasPicto ? 150 : 70;
  const gap = few ? 56 : 34;
  const area = areaFor(areaTop(props) + 10, BOX_L, BOX_W);
  const startFit = fitText(str(props.start), { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 44 });
  const endFit = fitText(str(props.end), { maxWidth: LABEL_W, maxLines: 1, max: 60, min: 44 });
  const layoutAt = (labelMax: number) => {
    const dates = marks.map((mark) =>
      mark.at && mark.label !== mark.at ? fitText(mark.at, { maxWidth: LABEL_W, maxLines: 1, max: Math.max(44, Math.round(labelMax * 0.78)), min: 44 }) : null,
    );
    const fits = marks.map((mark) => fitText(mark.label, { maxWidth: LABEL_W, maxLines: 2, max: labelMax, min: Math.min(48, labelMax), prefer: true }));
    const rows = fits.map((f, i) => (dates[i] ? stripHeight(dates[i]!.size) + 4 : 0) + stripsHeight(f.lines.length, f.size, 6));
    const height = capH + 64 + rows.reduce((a, b) => a + b, 0) + gap * (marks.length + 1);
    return { dates, fits, height };
  };
  const labelMax = largestFitting(few ? 76 : 64, 44, (m) => layoutAt(m).height <= area.height);
  const { dates, fits } = layoutAt(labelMax);
  const dateH = (i: number) => (dates[i] ? stripHeight(dates[i]!.size) + 4 : 0);

  return (
    <Stage>
      <FitBox area={area} maxScale={1.3}>
        <div style={{ position: "relative", display: "flex", flexDirection: "column", gap, maxWidth: BOX_W }}>
          <div style={{ position: "absolute", left: RAIL / 2 - 11, top: capH / 2, bottom: 32, width: 22 }}>
            <PaperShape kind="square" color="ink" size={1} w={22} h={10} seed="tl-axis" float={0.6} spin={0.1} motion={{ dy: 0, spin: 0, from: 0.96 }} style={{ width: 22, height: "100%" }} />
          </div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <Rail height={capH}>
              {hasPicto ? (
                <Picto name={props.picto} size={capH} rotate={-6} />
              ) : (
                <PaperShape kind="square" color="ink" size={capH} x={(RAIL - capH) / 2} rotate={8} seed="tl-start" />
              )}
            </Rail>
            {startFit.lines.length ? <Strips lines={startFit.lines} size={startFit.size} color="ink" align="flex-start" seed="tl-start-label" /> : null}
          </div>
          {marks.map((_, i) => {
            const at = enterFor(`marks.${i}`, items, from, to);
            const fit = fits[i];
            return (
              <div key={`mark-${i}`} style={{ display: "flex", alignItems: "flex-start", transform: beat && beat.index % Math.max(1, marks.length) === i ? `translateX(${46 * beat.wave}px) scale(${1 + 0.08 * beat.wave}) rotate(${-1.5 * beat.wave}deg)` : undefined, transformOrigin: "0 50%" }}>
                <Rail height={Math.max(70, dateH(i) || stripHeight(fit.size))}>
                  <PaperShape kind="circle" color={accent} size={70} x={(RAIL - 70) / 2} y={(Math.max(70, dateH(i) || stripHeight(fit.size)) - 70) / 2} enterAt={at} seed={`tl-dot-${i}`} float={1.5} motion={{ dy: 0, spin: 0, from: 0.9 }} />
                </Rail>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 4 }}>
                  {dates[i] ? (
                    <Strips lines={dates[i]!.lines} size={dates[i]!.size} color={accent} enterAt={at + 1} align="flex-start" seed={`tl-date-${i}`} motion={{ dx: -30, dy: 0 }} />
                  ) : null}
                  <Strips lines={fit.lines} size={fit.size} enterAt={at + 3} align="flex-start" seed={`tl-mark-${i}`} gap={6} motion={{ dx: -40, dy: 0 }} />
                </div>
              </div>
            );
          })}
          <div style={{ display: "flex", alignItems: "center" }}>
            <Rail height={64}>
              <PaperShape kind="square" color="ink" size={64} x={(RAIL - 64) / 2} rotate={-6} seed="tl-end" />
            </Rail>
            {endFit.lines.length ? <Strips lines={endFit.lines} size={endFit.size} color="ink" align="flex-start" seed="tl-end-label" /> : null}
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
