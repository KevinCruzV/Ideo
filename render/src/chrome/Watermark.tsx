import React from "react";
import { colors, fonts, layout, shade, SHADOW_X, SHADOW_Y } from "../theme";
import { textWidth } from "../text/fit";
import { cutEdge } from "../paper/motion";
import { MascotHead } from "../mascot/Character";

export const WATERMARK_HEAD = 44;
export const WATERMARK_SIZE = 30;
const WATERMARK_BRAND_EM = 1.38;
const WATERMARK_PAD = 12 + 22 + WATERMARK_HEAD + 10;

export const watermarkWidth = (text: string): number => WATERMARK_PAD + textWidth(text, WATERMARK_SIZE) * WATERMARK_BRAND_EM;

export const watermarkLeft = (text: string): number => layout.width - layout.safeRight - watermarkWidth(text);

export const Watermark: React.FC<{ text: string }> = ({ text }) => {
  const edge = cutEdge("watermark", 1.4);
  return (
    <div style={{ position: "absolute", top: layout.marginTop, right: layout.safeRight, transform: "rotate(2.5deg)" }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X}px, ${SHADOW_Y}px)`, background: shade, clipPath: edge }} />
      <div style={{ position: "absolute", inset: 0, background: colors.cream, clipPath: edge }} />
      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          gap: 10,
          color: colors.ink,
          fontFamily: fonts.brand,
          fontWeight: 800,
          fontSize: WATERMARK_SIZE,
          lineHeight: 1.2,
          padding: "6px 22px 6px 12px",
        }}
      >
        <MascotHead size={WATERMARK_HEAD} />
        <span>{text}</span>
      </div>
    </div>
  );
};
