import React from "react";
import { Img, staticFile } from "remotion";
import grainUrl from "../../public/grain.png";
import { cutEdge } from "../paper/motion";
import { usePaper } from "../paper/PaperContext";
import { photoFrame } from "../paper/supports";
import { colors, shade, SHADOW_X, SHADOW_Y } from "../theme";

export const PHOTO_W = 620;
export const PHOTO_H = 760;
const BORDER = 24;
const POLAROID_BOTTOM = 110;
const CORNER = 46;
const POLAROID_WHITE = "#fefdf9";

export const ART_W = 880;
export const ART_H = 760;

export const PhotoFrame: React.FC<{ src: string; seed: string; width?: number; height?: number; whole?: boolean }> = ({
  src,
  seed,
  width = PHOTO_W,
  height = PHOTO_H,
  whole = false,
}) => {
  const polaroid = photoFrame(usePaper()) === "polaroid";
  const outer = polaroid ? "none" : cutEdge(`${seed}-outer`, 2.4);
  const inner = polaroid ? "none" : cutEdge(`${seed}-inner`, 1.5);
  const hole = polaroid ? { top: BORDER, left: BORDER, right: BORDER, bottom: POLAROID_BOTTOM } : { inset: BORDER };
  return (
    <div style={{ position: "relative", width, height, transform: polaroid ? "rotate(-2.5deg)" : undefined }}>
      <div style={{ position: "absolute", inset: 0, transform: `translate(${SHADOW_X + 2}px, ${SHADOW_Y + 2}px)`, background: shade, clipPath: outer }} />
      <div style={{ position: "absolute", inset: 0, background: polaroid ? POLAROID_WHITE : colors.cream, clipPath: outer }} />
      {polaroid
        ? (["tl", "tr", "bl", "br"] as const).map((c) => (
            <div
              key={c}
              style={{
                position: "absolute",
                zIndex: 2,
                width: CORNER,
                height: CORNER,
                background: colors.ink,
                top: c[0] === "t" ? BORDER - 12 : undefined,
                bottom: c[0] === "b" ? POLAROID_BOTTOM - 12 : undefined,
                left: c[1] === "l" ? BORDER - 12 : undefined,
                right: c[1] === "r" ? BORDER - 12 : undefined,
                clipPath:
                  c === "tl" ? "polygon(0 0, 100% 0, 0 100%)" : c === "tr" ? "polygon(0 0, 100% 0, 100% 100%)" : c === "bl" ? "polygon(0 0, 0 100%, 100% 100%)" : "polygon(100% 0, 100% 100%, 0 100%)",
              }}
            />
          ))
        : null}
      <div style={{ position: "absolute", ...hole, clipPath: inner, overflow: "hidden" }}>
        <Img
          src={staticFile(src)}
          style={
            whole
              ? { width: "100%", height: "100%", objectFit: "contain", objectPosition: "50% 50%" }
              : { width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 20%", filter: "contrast(1.06) saturate(.85) sepia(.14)" }
          }
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `url(${grainUrl})`,
            backgroundSize: "384px 384px",
            mixBlendMode: "multiply",
            opacity: whole ? 0.25 : 0.55,
          }}
        />
      </div>
    </div>
  );
};
