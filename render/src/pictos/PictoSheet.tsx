import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../chrome/Background";
import { colors, fonts } from "../theme";
import { PICTOS } from "./library";
import { PictoArt } from "./Picto";

export const SHEET_COLS = 7;
export const SHEET_CELL = 220;
export const SHEET_W = SHEET_COLS * SHEET_CELL + 80;
export const SHEET_H = Math.ceil(PICTOS.length / SHEET_COLS) * (SHEET_CELL + 40) + 80;

export const PictoSheet: React.FC = () => (
  <AbsoluteFill>
    <Background />
    <div
      style={{
        position: "absolute",
        inset: 40,
        display: "grid",
        gridTemplateColumns: `repeat(${SHEET_COLS}, ${SHEET_CELL}px)`,
        gridAutoRows: `${SHEET_CELL + 40}px`,
      }}
    >
      {PICTOS.map((name) => (
        <div key={name} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
          <PictoArt name={name} size={170} />
          <span style={{ fontFamily: fonts.text, fontWeight: 700, fontSize: 24, color: colors.ink }}>{name}</span>
        </div>
      ))}
    </div>
  </AbsoluteFill>
);
