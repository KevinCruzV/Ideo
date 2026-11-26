import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { tornEdge } from "../paper/Sheet";
import { fitText } from "../text/fit";
import { AccentColor, colors, fonts, layout, onPaper, shade } from "../theme";

export const CARD_MAX = 45;
export const CARD_SHARE = 0.45;
export const CARD_EXIT = 7;
export const CARD_CAPS_WIDE = 1.15;
const CARD_W = layout.width + 80;
const CARD_PAD = 110;

export const cardLength = (duration: number): number => Math.min(CARD_MAX, Math.round(duration * CARD_SHARE));

export const cardFit = (text: string) =>
  fitText(text.toUpperCase(), { maxWidth: (layout.width - 2 * CARD_PAD) / CARD_CAPS_WIDE, maxLines: 3, max: 150, min: 70 });

export const ChapterCard: React.FC<{ text: string; accent: AccentColor; duration: number }> = ({ text, accent, duration }) => {
  const frame = useCurrentFrame();
  const length = cardLength(duration);
  if (frame >= length) return null;
  const fit = cardFit(text);
  const lift = interpolate(frame, [length - CARD_EXIT, length], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pop = interpolate(frame, [0, 5], [0.92, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const height = fit.lines.length * fit.size * 1.02 + 2 * CARD_PAD;
  const edge = tornEdge(`card-${text}`, 16, 3.5);
  return (
    <div style={{ position: "absolute", inset: 0, background: colors.ink, transform: `translateY(${-layout.height * lift * lift}px)` }}>
      <div
        style={{
          position: "absolute",
          left: -40,
          top: (layout.height - height) / 2 - 80,
          width: CARD_W,
          height,
          transform: `rotate(-4deg) scale(${pop})`,
        }}
      >
        <div style={{ position: "absolute", inset: 0, transform: "translate(10px, 14px)", background: shade, clipPath: edge }} />
        <div style={{ position: "absolute", inset: 0, background: colors[accent], clipPath: edge }} />
        <div
          style={{
            position: "relative",
            padding: `${CARD_PAD}px ${CARD_PAD + 40}px`,
            color: onPaper[accent],
            fontFamily: fonts.brand,
            fontWeight: 900,
            fontSize: fit.size,
            lineHeight: 1.02,
            letterSpacing: -fit.size * 0.03,
          }}
        >
          {fit.lines.map((line, i) => (
            <div key={`card-${i}`} style={{ whiteSpace: "nowrap" }}>{line}</div>
          ))}
        </div>
        <div style={{ position: "absolute", left: 70, top: -34, width: 230, height: 64, background: colors.cream, opacity: 0.8, transform: "rotate(-16deg)" }} />
        <div style={{ position: "absolute", right: 110, bottom: -30, width: 230, height: 64, background: colors.cream, opacity: 0.8, transform: "rotate(-12deg)" }} />
      </div>
    </div>
  );
};
