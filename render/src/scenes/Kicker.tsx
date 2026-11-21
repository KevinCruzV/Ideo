import React from "react";
import { PaperStrip } from "../paper/PaperStrip";
import { fitText } from "../text/fit";
import { BOX_L, BOX_W } from "./Stage";

export const KICKER_SIZE = 38;

export const Kicker: React.FC<{ text: string }> = ({ text }) => {
  const clean = text.trim().slice(0, 28);
  if (!clean) return null;
  const fit = fitText(clean.toUpperCase(), { maxWidth: BOX_W * 0.9, maxLines: 1, max: KICKER_SIZE, min: 28 });
  return (
    <div style={{ position: "absolute", left: BOX_L, top: 0 }}>
      <PaperStrip
        text={fit.lines[0] ?? clean}
        color="ink"
        fontSize={fit.size}
        rotate={-1.5}
        seed={`kicker-${clean}`}
        enterAt={-3}
        float={1.5}
        spacing={2}
        motion={{ dx: -50, dy: 0, spin: -3 }}
      />
    </div>
  );
};
