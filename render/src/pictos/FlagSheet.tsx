import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "../chrome/Background";
import { colors, fonts } from "../theme";
import { PictoArt } from "./Picto";

export const SHEET_FLAGS = [
  "br", "ru", "in", "cn", "za", "us", "su", "eu",
  "un", "fr", "gb", "de", "it", "es", "pt", "jp",
  "kr", "kp", "ca", "mx", "ar", "cl", "eg", "sa",
  "ir", "il", "ps", "tr", "ua", "pl", "se", "ch",
  "ng", "ke", "et", "au", "nz", "id", "vn", "cu",
];

const COLS = 8;
const CELL = 200;
export const FLAG_SHEET_W = COLS * CELL + 80;
export const FLAG_SHEET_H = Math.ceil(SHEET_FLAGS.length / COLS) * (CELL + 30) + 80;

export const FlagSheet: React.FC = () => (
  <AbsoluteFill>
    <Background />
    <div style={{ position: "absolute", inset: 40, display: "grid", gridTemplateColumns: `repeat(${COLS}, ${CELL}px)`, gridAutoRows: `${CELL + 30}px` }}>
      {SHEET_FLAGS.map((code) => (
        <div key={code} style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4 }}>
          <PictoArt name={`flag:${code}`} size={160} />
          <span style={{ fontFamily: fonts.text, fontWeight: 700, fontSize: 24, color: colors.ink }}>{code}</span>
        </div>
      ))}
    </div>
  </AbsoluteFill>
);
