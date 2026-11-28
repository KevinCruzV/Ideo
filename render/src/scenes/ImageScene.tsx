import React from "react";
import { Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { SHEET_BOTTOM, SHEET_LEFT, SHEET_RIGHT, SHEET_TOP } from "../paper/Sheet";
import { fitText } from "../text/fit";
import { colors, shade, SHADOW_X, SHADOW_Y } from "../theme";
import { photoSource, str } from "./coerce";
import type { SceneProps } from "./registry";
import { BOX_W } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

export const IMAGE_ZOOM = 0.08;
const CAPTION_BOTTOM = 90;

export const ImageScene: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const image = photoSource(props.image);
  const caption = fitText(str(props.caption), { maxWidth: BOX_W, maxLines: 2, max: 80, min: 48, prefer: true });
  const captionAt = enterFor("caption", items, from, to);
  const span = Math.max(1, to - from);
  const zoom = 1 + IMAGE_ZOOM * interpolate(frame, [0, span], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const reveal = interpolate(frame, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const box = { left: SHEET_LEFT, top: SHEET_TOP, width: SHEET_RIGHT - SHEET_LEFT, height: SHEET_BOTTOM - SHEET_TOP };

  return (
    <>
      <div style={{ position: "absolute", ...box, transform: `translate(${SHADOW_X}px, ${SHADOW_Y}px)`, background: shade }} />
      <div style={{ position: "absolute", ...box, overflow: "hidden", background: colors.ink, opacity: reveal }}>
        {image ? (
          <>
            <Img
              src={staticFile(image)}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: "blur(36px) brightness(.55)", transform: "scale(1.2)" }}
            />
            <Img
              src={staticFile(image)}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "contain", transform: `scale(${zoom})` }}
            />
          </>
        ) : null}
      </div>
      {caption.lines.length ? (
        <div style={{ position: "absolute", left: box.left, width: box.width, top: box.top + box.height - CAPTION_BOTTOM, display: "flex", justifyContent: "center" }}>
          <div style={{ transform: "translateY(-100%)" }}>
            <Strips lines={caption.lines} size={caption.size} enterAt={captionAt} seed="image-caption" />
          </div>
        </div>
      ) : null}
    </>
  );
};
