import React from "react";
import { AbsoluteFill } from "remotion";
import persons from "../../fixtures/persons.json";
import { Background } from "../chrome/Background";
import { accentForIndex, colors, fonts } from "../theme";
import { bustHeight, PersonBust } from "./PersonBust";
import { lookOf } from "./personLook";

const COLS = 4;
const CELL_W = 360;
const BUST_W = 320;
const CELL_H = Math.round(bustHeight(BUST_W) + 80);
export const PERSON_SHEET_W = COLS * CELL_W + 80;
export const PERSON_SHEET_H = Math.ceil(persons.length / COLS) * CELL_H + 80;

const describe = (p: Record<string, unknown>): string =>
  Object.entries(p)
    .map(([k, v]) => `${k.replace("hair_color", "couleur").replace("outfit", "tenue")}: ${String(v)}`)
    .join(" · ");

export const PersonSheet: React.FC = () => (
  <AbsoluteFill>
    <Background />
    <div style={{ position: "absolute", inset: 40, display: "grid", gridTemplateColumns: `repeat(${COLS}, ${CELL_W}px)`, gridAutoRows: `${CELL_H}px` }}>
      {persons.map((p, i) => {
        const accent = accentForIndex(i);
        return (
          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <div style={{ position: "relative", width: BUST_W, height: bustHeight(BUST_W) }}>
              <div style={{ position: "absolute", left: 50, top: bustHeight(BUST_W) * 0.2, width: 220, height: 220, borderRadius: "50%", background: colors[accent] }} />
              <div style={{ position: "absolute", inset: 0 }}>
                <PersonBust width={BUST_W} initials="AB" badge={colors.yellow} badgeInk={colors.ink} look={lookOf(p)} accent={accent} seed={`sheet-${i}`} />
              </div>
            </div>
            <span style={{ fontFamily: fonts.text, fontWeight: 600, fontSize: 15, color: colors.ink, textAlign: "center", width: CELL_W - 20 }}>{describe(p)}</span>
          </div>
        );
      })}
    </div>
  </AbsoluteFill>
);
