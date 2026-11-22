import React from "react";
import { Img, staticFile } from "remotion";
import grainUrl from "../../public/grain.png";
import { cutEdge } from "../paper/motion";
import { colors, shade, SHADOW_X, SHADOW_Y } from "../theme";

export const PHOTO_W = 620;
export const PHOTO_H = 760;
const BORDER = 24;

export const PhotoFrame: React.FC<{ src: string; seed: string }> = ({ src, seed }) => {
  const outer = cutEdge(`${seed}-outer`, 2.4);
  const inner = cutEdge(`${seed}-inner`, 1.5);
  return (
    <div style={{ position: "relative", width: PHOTO_W, height: PHOTO_H }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X + 2}px, ${SHADOW_Y + 2}px)`, background: shade, clipPath: outer }} />
      <div style={{ position: "absolute", inset: 0, background: colors.cream, clipPath: outer }} />
      <div style={{ position: "absolute", inset: BORDER, clipPath: inner, overflow: "hidden" }}>
        <Img
          src={staticFile(src)}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 20%", filter: "contrast(1.06) saturate(.85) sepia(.14)" }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `url(${grainUrl})`,
            backgroundSize: "384px 384px",
            mixBlendMode: "multiply",
            opacity: 0.55,
          }}
        />
      </div>
    </div>
  );
};
