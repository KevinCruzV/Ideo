import React from "react";
import { AbsoluteFill } from "remotion";
import { Background } from "./chrome/Background";
import { Watermark } from "./chrome/Watermark";
import { MascotHead } from "./mascot/Character";
import { tornEdge } from "./paper/Sheet";
import { hasVisual, PictoArt } from "./pictos/Picto";
import { initials, photoSource, str } from "./scenes/coerce";
import { PHOTO_H, PHOTO_W, PhotoFrame } from "./scenes/PhotoFrame";
import { lookOf } from "./scenes/personLook";
import { bustHeight, CLOSE_VIEW, PersonBust } from "./scenes/PersonBust";
import { fitText } from "./text/fit";
import { AccentColor, accentCycle, colors, fonts, groundOf, layout, moodOf, onPaper, setMood, shade } from "./theme";

export type CoverLook = Record<string, unknown> & { name?: string };

export type CoverProps = {
  title: string;
  hook?: string;
  picto?: string | null;
  photo?: string | null;
  look?: CoverLook | null;
  watermark: string;
  part: number;
  total: number;
  label: string;
  mood?: "dark";
};

export const COVER_FRAMES = 60;
export const ART_SIZE = 620;
export const DISK = ART_SIZE + 60;
export const PHOTO_SCALE = DISK / PHOTO_H;
export const TAG_SIZE = 52;

export type ArtKind = "photo" | "bust" | "picto" | "mascot";

export const artKind = (photo: unknown, picto: string | null | undefined, look?: CoverLook | null): ArtKind => {
  if (photoSource(photo)) return "photo";
  if (look) return "bust";
  return hasVisual(picto) ? "picto" : "mascot";
};

const BUST_W = 420;
const BUST_H = bustHeight(BUST_W, CLOSE_VIEW);

export const coverAccent = (title: string): AccentColor => {
  let sum = 0;
  for (const ch of title) sum = (sum * 31 + ch.codePointAt(0)!) % 9973;
  return accentCycle[sum % accentCycle.length];
};

export const partTag = (label: string, part: number, total: number): string | null =>
  total > 1 ? `${label} ${part}/${total}` : null;

export const splitHook = (hook: string): { head: string; sub: string | null } => {
  const text = hook.trim();
  const cut = text.search(/[,:](?=\s)/);
  if (cut > 0) {
    const head = text.slice(0, cut).trim();
    const sub = text.slice(cut + 1).trim();
    if (head && sub) return { head, sub };
  }
  return { head: text, sub: null };
};

const namesPart = (hook: string, label: string, part: number): boolean =>
  new RegExp(`${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*${part}(?!\\d)`, "i").test(hook);

export const coverText = (
  title: string,
  hook: string | undefined,
  part: number,
  total: number,
  label: string,
): { head: string; sub: string | null; tag: string | null } => {
  const { head, sub } = splitHook(hook ?? "");
  return { head: head || title, sub, tag: namesPart(hook ?? "", label, part) ? null : partTag(label, part, total) };
};

export const SHEET_X = 40;
export const CROP_TOP = 300;
export const CROP_BOTTOM = 1640;
export const CAPS_WIDE = 1.15;
export const SHEET_W = layout.width - 2 * SHEET_X;
export const SHEET_PAD_X = 64;
export const SHEET_PAD_Y = 84;
export const HEAD_LINE = 1.02;
export const ART_OVERLAP = 150;
export const ART_RIGHT = 40;
const LABEL_MAX_W = 640;

export const coverHeadFit = (head: string) =>
  fitText(head.toUpperCase(), { maxWidth: (SHEET_W - 2 * SHEET_PAD_X) / CAPS_WIDE, maxLines: 5, max: 140, min: 60 });

export const coverSheetHeight = (lines: number, size: number): number => lines * size * HEAD_LINE + 2 * SHEET_PAD_Y;

export const coverLayout = (sheetH: number, artH: number): { sheetY: number; artTop: number } => {
  const total = sheetH - ART_OVERLAP + artH;
  const sheetY = Math.round(Math.max(CROP_TOP, (CROP_TOP + CROP_BOTTOM - total) / 2));
  return { sheetY, artTop: sheetY + sheetH - ART_OVERLAP };
};

const Art: React.FC<{ art: ArtKind; photo?: string | null; picto?: string | null; look?: CoverLook | null; accent: AccentColor }> = ({ art, photo, picto, look, accent }) => {
  const bustLook = React.useMemo(() => lookOf(look ?? {}), [look]);
  if (art === "photo") {
    return (
      <div style={{ width: PHOTO_W, height: PHOTO_H, transform: `scale(${PHOTO_SCALE})`, transformOrigin: "0 0" }}>
        <PhotoFrame src={photo as string} seed="cover-photo" />
      </div>
    );
  }
  if (art === "bust") {
    return (
      <PersonBust
        width={BUST_W}
        initials={initials(str(look?.name, "?"))}
        badge={accent === "yellow" ? colors.red : colors.yellow}
        badgeInk={onPaper[accent === "yellow" ? "red" : "yellow"]}
        look={bustLook}
        accent={accent}
        view={CLOSE_VIEW}
        seed="cover-bust"
      />
    );
  }
  return art === "picto" ? <PictoArt name={picto} size={ART_SIZE} /> : <MascotHead size={ART_SIZE * 0.8} />;
};

const artBox = (art: ArtKind): { w: number; h: number } =>
  art === "photo" ? { w: PHOTO_W * PHOTO_SCALE, h: DISK } : art === "bust" ? { w: BUST_W, h: BUST_H } : { w: ART_SIZE, h: ART_SIZE };

export const Cover: React.FC<CoverProps> = ({ title, hook, picto, photo, look, watermark, part, total, label, mood }) => {
  setMood(moodOf(mood));
  const accent = coverAccent(title);
  const text = coverText(title, hook, part, total, label);
  const head = coverHeadFit(text.head);
  const sub = fitText(text.sub ?? "", { maxWidth: LABEL_MAX_W, maxLines: 3, max: 58, min: 40, prefer: true });
  const art = artKind(photo, picto, look);
  const box = artBox(art);
  const sheetH = coverSheetHeight(head.lines.length, head.size);
  const { sheetY, artTop } = coverLayout(sheetH, box.h);
  const edge = tornEdge("cover-sheet");
  return (
    <AbsoluteFill>
      <Background color={groundOf(accent)} />
      {text.tag ? (
        <div style={{ position: "absolute", left: SHEET_X + 24, top: sheetY - 110, background: colors.ink, color: colors.cream, fontFamily: fonts.brand, fontWeight: 700, fontSize: TAG_SIZE * 0.7, letterSpacing: 2, padding: "10px 24px", borderRadius: 999, transform: "rotate(-3deg)" }}>
          {text.tag.toUpperCase()}
        </div>
      ) : null}
      <div style={{ position: "absolute", left: SHEET_X, top: sheetY, width: SHEET_W, height: sheetH, transform: "rotate(-2.5deg)" }}>
        <div style={{ position: "absolute", inset: 0, transform: "translate(10px, 14px)", background: shade, clipPath: edge }} />
        <div style={{ position: "absolute", inset: 0, background: colors.cream, clipPath: edge }} />
        <div style={{ position: "relative", padding: `${SHEET_PAD_Y}px ${SHEET_PAD_X}px`, fontFamily: fonts.brand, fontWeight: 900, fontSize: head.size, lineHeight: HEAD_LINE, letterSpacing: -head.size * 0.025, color: colors.ink }}>
          {head.lines.map((line, i) => (
            <div key={`head-${i}`} style={{ whiteSpace: "nowrap" }}>{line}</div>
          ))}
        </div>
        <div style={{ position: "absolute", left: 40, top: -30, width: 210, height: 60, background: colors.cream, opacity: 0.8, transform: "rotate(-14deg)" }} />
        <div style={{ position: "absolute", right: 30, top: -24, width: 210, height: 60, background: colors.cream, opacity: 0.8, transform: "rotate(10deg)" }} />
      </div>
      <div style={{ position: "absolute", left: layout.width - ART_RIGHT - box.w, top: artTop, width: box.w, height: box.h, transform: "rotate(8deg)", filter: `drop-shadow(12px 16px 0 ${shade})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Art art={art} photo={photo} picto={picto} look={look} accent={accent} />
      </div>
      {sub.lines.length > 0 ? (
        <div style={{ position: "absolute", left: SHEET_X + 24, top: sheetY + sheetH + 50, maxWidth: LABEL_MAX_W, background: colors.ink, color: colors.cream, fontFamily: fonts.text, fontWeight: 800, fontSize: sub.size, lineHeight: 1.12, padding: "18px 28px", transform: "rotate(2deg)", boxShadow: `8px 10px 0 ${shade}` }}>
          {sub.lines.map((line, i) => (
            <div key={`sub-${i}`}>{line}</div>
          ))}
        </div>
      ) : null}
      <Watermark text={watermark} />
    </AbsoluteFill>
  );
};
