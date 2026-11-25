import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "./chrome/Background";
import { Watermark } from "./chrome/Watermark";
import { MascotHead } from "./mascot/Character";
import { PaperStrip, stripHeight } from "./paper/PaperStrip";
import { hasVisual, PictoArt } from "./pictos/Picto";
import { Backdrop } from "./scenes/Backdrop";
import { photoSource } from "./scenes/coerce";
import { PHOTO_H, PHOTO_W, PhotoFrame } from "./scenes/PhotoFrame";
import { Strips, stripsHeight } from "./scenes/Strips";
import { fitText } from "./text/fit";
import { AccentColor, accentCycle, content, layout, moodOf, setMood } from "./theme";

export type CoverProps = {
  title: string;
  hook?: string;
  picto?: string | null;
  photo?: string | null;
  watermark: string;
  part: number;
  total: number;
  label: string;
  mood?: "dark";
};

export const COVER_FRAMES = 60;
export const TITLE_TOP = 260;
export const ART_SIZE = 400;
export const DISK = ART_SIZE + 130;
export const GAP = 70;
export const PHOTO_SCALE = DISK / PHOTO_H;
export const TAG_SIZE = 52;
export const TAG_GAP = 28;

export type ArtKind = "photo" | "picto" | "mascot";

export const artKind = (photo: unknown, picto: string | null | undefined): ArtKind => {
  if (photoSource(photo)) return "photo";
  return hasVisual(picto) ? "picto" : "mascot";
};

export const coverAccent = (title: string): AccentColor => {
  let sum = 0;
  for (const ch of title) sum = (sum * 31 + ch.codePointAt(0)!) % 9973;
  return accentCycle[sum % accentCycle.length];
};

export const partTag = (label: string, part: number, total: number): string | null =>
  total > 1 ? `${label} ${part}/${total}` : null;

export const Cover: React.FC<CoverProps> = ({ title, hook, picto, photo, watermark, part, total, label, mood }) => {
  setMood(moodOf(mood));
  const accent = coverAccent(title);
  const head = fitText(title, { maxWidth: content.width - 40, maxLines: 3, max: 112, min: 68 });
  const ask = fitText(hook ?? "", { maxWidth: content.width - 40, maxLines: 3, max: 62, min: 44 });
  const art = artKind(photo, picto);
  const tag = partTag(label, part, total);
  const tagSpace = tag ? stripHeight(TAG_SIZE) + TAG_GAP : 0;
  const titleBottom = TITLE_TOP + tagSpace + stripsHeight(head.lines.length, head.size);
  const artCy = titleBottom + GAP + DISK / 2;
  const hookTop = artCy + DISK / 2 + GAP;
  return (
    <AbsoluteFill>
      <Background />
      <div style={{ position: "absolute", left: content.left, top: TITLE_TOP, width: content.width }}>
        {tag ? (
          <PaperStrip text={tag} color="ink" fontSize={TAG_SIZE} rotate={-3} seed="cover-tag" style={{ marginBottom: TAG_GAP }} />
        ) : null}
        <Strips lines={head.lines} size={head.size} color={accent} align="flex-start" seed="cover-title" tilt={-1.5} />
      </div>
      {art === "photo" ? (
        <div
          style={{
            position: "absolute",
            left: layout.width / 2 - PHOTO_W / 2,
            top: artCy - PHOTO_H / 2,
            width: PHOTO_W,
            height: PHOTO_H,
            transform: `rotate(-2deg) scale(${PHOTO_SCALE})`,
          }}
        >
          <PhotoFrame src={photo as string} seed="cover-photo" />
        </div>
      ) : (
        <>
          <Backdrop color="cream" size={DISK} cx={layout.width / 2} cy={artCy} seed="cover-disk" turn={0} />
          <div
            style={{
              position: "absolute",
              left: layout.width / 2 - ART_SIZE / 2,
              top: artCy - ART_SIZE / 2,
              width: ART_SIZE,
              height: ART_SIZE,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {art === "picto" ? <PictoArt name={picto} size={ART_SIZE} /> : <MascotHead size={ART_SIZE * 0.8} />}
          </div>
        </>
      )}
      {ask.lines.length > 0 ? (
        <div style={{ position: "absolute", left: content.left, top: hookTop, width: content.width }}>
          <Strips lines={ask.lines} size={ask.size} color="ink" align="center" seed="cover-hook" />
        </div>
      ) : null}
      <Watermark text={watermark} />
    </AbsoluteFill>
  );
};
