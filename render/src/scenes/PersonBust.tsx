import React from "react";
import { useCurrentFrame } from "remotion";
import { Cutter, Pt } from "../pictos/cut";
import { breath, isBlinking } from "../mascot/pose";
import { useBeat } from "./beats";
import { AccentColor, colors, fonts, shade } from "../theme";
import { HAIR_TONES, HIDES_HAIR_TOP, NEUTRAL_LOOK, PersonLook, SKIN_TONES } from "./personLook";

export const BUST_VIEW = { x: 0, y: -46, w: 200, h: 174 } as const;

type Shape = { d: string; fill: string; shadow?: boolean };

const HEAD = { cx: 100, cy: 40, rx: 34, ry: 37 };

const ring = (cx: number, cy: number, rx: number, ry: number, from = 0, to = 360, steps = 28): Pt[] =>
  Array.from({ length: steps + 1 }, (_, i) => {
    const a = ((from + ((to - from) * i) / steps) * Math.PI) / 180;
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  });

const bumps = (cx: number, cy: number, rx: number, ry: number, from: number, to: number, count: number, depth: number): Pt[] => {
  const pts: Pt[] = [];
  const steps = count * 6;
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    const a = ((from + (to - from) * t) * Math.PI) / 180;
    const bump = 1 + depth * Math.abs(Math.sin(t * count * Math.PI));
    pts.push([cx + rx * bump * Math.cos(a), cy + ry * bump * Math.sin(a)]);
  }
  return pts;
};

const spikes = (cx: number, cy: number, rx: number, ry: number, from: number, to: number, count: number, depth: number): Pt[] =>
  Array.from({ length: count * 2 + 1 }, (_, i) => {
    const a = ((from + ((to - from) * i) / (count * 2)) * Math.PI) / 180;
    const r = i % 2 === 1 ? 1 + depth : 1;
    return [cx + rx * r * Math.cos(a), cy + ry * r * Math.sin(a)];
  });

const alternate = (accent: AccentColor): string => (accent === "blue" ? colors.red : colors.blue);

const outfitShapes = (k: Cutter, look: PersonLook, accent: AccentColor): Shape[] => {
  const shoulders: Pt[] = [
    [16, 128],
    [22, 98],
    [38, 85],
    [62, 79],
    [100, 77],
    [138, 79],
    [162, 85],
    [178, 98],
    [184, 128],
  ];
  const body = (fill: string): Shape => ({ d: k.path(shoulders), fill, shadow: true });
  const alt = alternate(accent);
  const skin = SKIN_TONES[look.skin];
  switch (look.outfit) {
    case "uniform":
      return [
        body(alt),
        { d: k.path([[84, 77], [116, 77], [118, 90], [82, 90]]), fill: colors.ink },
        ...[96, 106, 116].map((y) => ({ d: k.path(ring(100, y, 3.4, 3.4, 0, 360, 10)), fill: colors.yellow })),
        { d: k.path([[30, 86], [62, 80], [64, 88], [32, 95]]), fill: colors.yellow, shadow: true },
        { d: k.path([[170, 86], [138, 80], [136, 88], [168, 95]]), fill: colors.yellow, shadow: true },
      ];
    case "robe":
      return [
        body(alt),
        { d: k.path([[70, 78], [100, 100], [130, 78], [124, 72], [100, 86], [76, 72]]), fill: colors.cream, shadow: true },
        { d: k.path([[88, 88], [112, 88], [106, 112], [94, 112]]), fill: colors.cream, shadow: true },
      ];
    case "lab-coat":
      return [
        body(colors.cream),
        { d: k.path([[82, 78], [118, 78], [100, 108]]), fill: alt },
        { d: k.path([[80, 78], [100, 108], [90, 124], [66, 82]]), fill: colors.cream, shadow: true },
        { d: k.path([[120, 78], [134, 82], [110, 124], [100, 108]]), fill: colors.cream, shadow: true },
        { d: k.path([[136, 104], [154, 104], [154, 110], [136, 110]]), fill: "rgba(31,26,20,.18)" },
      ];
    case "casual":
      return [body(alt), { d: k.path(ring(100, 78, 17, 8, 0, 180, 14).concat([[83, 76], [117, 76]])), fill: colors.cream, shadow: true }];
    case "toga":
      return [
        body(colors.cream),
        { d: k.path([[60, 80], [92, 78], [150, 128], [112, 128]]), fill: alt, shadow: true },
        { d: k.path([[96, 78], [118, 78], [176, 128], [160, 128]]), fill: "rgba(31,26,20,.14)" },
      ];
    case "armor":
      return [
        body(colors.ink),
        { d: k.path([[64, 82], [136, 82], [130, 128], [70, 128]]), fill: "#3b352d", shadow: true },
        ...[96, 110].map((y) => ({ d: k.path([[68, y], [132, y], [131, y + 3], [69, y + 3]]), fill: colors.cream })),
        { d: k.path(ring(40, 94, 24, 14, 160, 380, 16)), fill: "#3b352d", shadow: true },
        { d: k.path(ring(160, 94, 24, 14, 160, 380, 16)), fill: "#3b352d", shadow: true },
        ...[40, 160].map((x) => ({ d: k.path(ring(x, 90, 3, 3, 0, 360, 8)), fill: colors.cream })),
      ];
    case "dress":
      return [
        body(alt),
        { d: k.path(ring(100, 76, 26, 20, 0, 180, 18).concat([[74, 74], [126, 74]])), fill: skin, shadow: false },
        { d: k.path(ring(100, 76, 26, 20, 0, 180, 18).map(([x, y]) => [x, y + 3] as Pt).concat(ring(100, 76, 26, 20, 180, 0, 18).map(([x, y]) => [x, y + 3] as Pt))), fill: colors.cream },
      ];
    case "suit":
    default:
      return [
        body(colors.ink),
        { d: k.path([[80, 78], [120, 78], [100, 112]]), fill: colors.cream },
        { d: k.path([[96, 84], [104, 84], [107, 116], [100, 124], [93, 116]]), fill: alt },
        { d: k.path([[80, 78], [100, 112], [88, 126], [70, 82]]), fill: colors.ink, shadow: true },
        { d: k.path([[120, 78], [130, 82], [112, 126], [100, 112]]), fill: colors.ink, shadow: true },
      ];
  }
};

const backHair = (k: Cutter, look: PersonLook, hidden: boolean): Shape[] => {
  const fill = HAIR_TONES[look.hairColor];
  switch (look.hair) {
    case "long":
      return [{ d: k.path([[64, 26], [136, 26], [146, 92], [124, 100], [100, 90], [76, 100], [54, 92]]), fill, shadow: true }];
    case "curly":
      return hidden
        ? [{ d: k.path(bumps(100, 42, 44, 44, 150, 390, 11, 0.09).filter(([, y]) => y > 26)), fill, shadow: true }]
        : [{ d: k.path(bumps(100, 42, 44, 44, 150, 390, 11, 0.09)), fill, shadow: true }];
    case "wild":
      return hidden
        ? [{ d: k.path(spikes(100, 40, 50, 46, 140, 400, 13, 0.18).filter(([, y]) => y > 26)), fill, shadow: true }]
        : [{ d: k.path(spikes(100, 40, 50, 46, 140, 400, 13, 0.18)), fill, shadow: true }];
    case "bun":
      return hidden ? [] : [{ d: k.path(ring(100, 2, 15, 13)), fill, shadow: true }];
    default:
      return [];
  }
};

const frontHair = (k: Cutter, look: PersonLook, hidden: boolean): Shape[] => {
  const fill = HAIR_TONES[look.hairColor];
  const sides: Shape[] = [
    { d: k.path([[66, 28], [74, 26], [74, 50], [67, 48]]), fill },
    { d: k.path([[134, 28], [126, 26], [126, 50], [133, 48]]), fill },
  ];
  if (look.hair === "none") return [];
  if (hidden || look.hair === "crown-bald") return sides;
  switch (look.hair) {
    case "side":
      return [
        { d: k.path([[64, 40], [64, 22], [78, 8], [100, 4], [124, 8], [136, 22], [136, 40], [130, 26], [96, 20], [112, 30], [80, 24], [70, 32]]), fill, shadow: true },
      ];
    case "long":
      return [{ d: k.path([[64, 42], [66, 20], [82, 7], [100, 4], [118, 7], [134, 20], [136, 42], [126, 22], [100, 16], [74, 22]]), fill, shadow: true }];
    case "curly":
      return [{ d: k.path(bumps(100, 30, 36, 26, 185, 355, 7, 0.14).concat([[132, 30], [68, 30]])), fill, shadow: true }];
    case "wild":
      return [{ d: k.path(spikes(100, 26, 38, 24, 180, 360, 7, 0.22).concat([[134, 30], [66, 30]])), fill, shadow: true }];
    case "bun":
      return [{ d: k.path([[64, 38], [66, 20], [82, 7], [100, 4], [118, 7], [134, 20], [136, 38], [128, 24], [100, 18], [72, 24]]), fill, shadow: true }];
    case "short":
    default:
      return [{ d: k.path([[64, 40], [66, 22], [80, 10], [100, 6], [120, 10], [134, 22], [136, 40], [128, 30], [110, 26], [86, 28], [72, 34]]), fill, shadow: true }];
  }
};

const facialShapes = (k: Cutter, look: PersonLook): Shape[] => {
  const fill = HAIR_TONES[look.hairColor];
  const moustache: Shape = { d: k.path([[86, 56], [100, 52], [114, 56], [116, 60], [100, 57], [84, 60]]), fill };
  switch (look.facial) {
    case "moustache":
      return [moustache];
    case "beard":
      return [{ d: k.path([[66, 44], [72, 46], [80, 62], [100, 66], [120, 62], [128, 46], [134, 44], [132, 66], [118, 82], [100, 88], [82, 82], [68, 66]]), fill, shadow: true }, moustache];
    case "goatee":
      return [{ d: k.path([[92, 63], [108, 63], [106, 78], [100, 82], [94, 78]]), fill }, moustache];
    case "sideburns":
      return [
        { d: k.path([[66, 40], [74, 40], [76, 62], [69, 60]]), fill },
        { d: k.path([[134, 40], [126, 40], [124, 62], [131, 60]]), fill },
      ];
    default:
      return [];
  }
};

const hatShapes = (k: Cutter, look: PersonLook, accent: AccentColor): Shape[] => {
  const alt = alternate(accent);
  switch (look.hat) {
    case "cap":
      return [
        { d: k.path(ring(100, 24, 37, 26, 180, 360, 18).concat([[137, 26], [63, 26]])), fill: alt, shadow: true },
        { d: k.path([[98, 18], [150, 20], [160, 28], [100, 30]]), fill: colors.ink, shadow: true },
        { d: k.path(ring(100, -1, 4, 3, 0, 360, 8)), fill: colors.ink },
      ];
    case "kepi":
      return [
        { d: k.path([[70, 26], [74, -6], [126, -10], [130, 26]]), fill: alt, shadow: true },
        { d: k.path([[69, 16], [131, 16], [131, 26], [69, 26]]), fill: colors.ink },
        { d: k.path([[66, 25], [134, 25], [126, 33], [74, 33]]), fill: colors.ink, shadow: true },
      ];
    case "bicorne":
      return [
        { d: k.path([[38, 24], [66, 4], [100, -8], [134, 4], [162, 24], [134, 20], [100, 16], [66, 20]]), fill: colors.ink, shadow: true },
        { d: k.path([[50, 22], [70, 10], [100, 2], [130, 10], [150, 22], [130, 18], [100, 13], [70, 18]]), fill: "#3b352d" },
        { d: k.path([[60, 22], [100, 14], [140, 22], [140, 25], [100, 18], [60, 25]]), fill: colors.yellow },
      ];
    case "crown":
      return [
        { d: k.path([[70, 16], [68, -14], [80, -2], [90, -18], [100, -4], [110, -18], [120, -2], [132, -14], [130, 16]]), fill: colors.yellow, shadow: true },
        { d: k.path([[69, 8], [131, 8], [131, 17], [69, 17]]), fill: colors.red },
        ...[82, 100, 118].map((x) => ({ d: k.path(ring(x, 12.5, 3, 3, 0, 360, 8)), fill: colors.cream })),
      ];
    case "helmet":
      return [
        { d: k.path(ring(100, 30, 40, 36, 180, 360, 20).concat([[140, 32], [60, 32]])), fill: "#3b352d", shadow: true },
        { d: k.path([[56, 26], [144, 26], [146, 34], [54, 34]]), fill: colors.ink, shadow: true },
        { d: k.path([[96, 30], [104, 30], [103, 54], [97, 54]]), fill: colors.ink, shadow: true },
        ...[66, 82, 118, 134].map((x) => ({ d: k.path(ring(x, 30, 2.4, 2.4, 0, 360, 8)), fill: colors.cream })),
      ];
    case "top-hat":
      return [
        { d: k.path([[74, 20], [76, -40], [124, -40], [126, 20]]), fill: colors.ink, shadow: true },
        { d: k.path([[75, 8], [125, 8], [125, 16], [75, 16]]), fill: alt },
        { d: k.path([[56, 18], [144, 18], [140, 26], [60, 26]]), fill: colors.ink, shadow: true },
      ];
    case "beret":
      return [
        { d: k.path(ring(96, 16, 40, 14, 0, 360, 22)), fill: alt, shadow: true },
        { d: k.path([[96, 2], [100, -6], [104, 2]]), fill: alt },
      ];
    case "turban":
      return [
        { d: k.path(ring(100, 18, 40, 30, 180, 360, 20).concat([[140, 26], [60, 26]])), fill: colors.cream, shadow: true },
        { d: k.path([[62, 18], [100, -4], [138, 14], [136, 20], [100, 4], [64, 24]]), fill: "rgba(31,26,20,.16)" },
        { d: k.path([[66, 6], [108, -10], [132, 0], [130, 6], [106, -3], [70, 12]]), fill: "rgba(31,26,20,.16)" },
        { d: k.path(ring(100, 12, 7, 7, 0, 360, 10)), fill: alt, shadow: true },
      ];
    case "laurel":
      return [
        ...Array.from({ length: 6 }, (_, i) => {
          const a = 200 + i * 14;
          const r = (a * Math.PI) / 180;
          const x = 100 + 38 * Math.cos(r);
          const y = 30 + 30 * Math.sin(r);
          return { d: k.path(ring(x, y, 8, 4, 0, 360, 10).map(([px, py]) => rotate([px, py], [x, y], a + 90))), fill: colors.yellow, shadow: true };
        }),
        ...Array.from({ length: 6 }, (_, i) => {
          const a = 340 - i * 14;
          const r = (a * Math.PI) / 180;
          const x = 100 + 38 * Math.cos(r);
          const y = 30 + 30 * Math.sin(r);
          return { d: k.path(ring(x, y, 8, 4, 0, 360, 10).map(([px, py]) => rotate([px, py], [x, y], a + 90))), fill: colors.yellow, shadow: true };
        }),
      ];
    case "wig":
      return [
        { d: k.path(bumps(100, 22, 40, 26, 180, 360, 6, 0.12).concat([[140, 28], [60, 28]])), fill: "#ece6da", shadow: true },
        ...[0, 1, 2].flatMap((i) => [
          { d: k.path(ring(64, 34 + i * 14, 9, 7, 0, 360, 12)), fill: "#ece6da", shadow: true },
          { d: k.path(ring(136, 34 + i * 14, 9, 7, 0, 360, 12)), fill: "#ece6da", shadow: true },
        ]),
      ];
    default:
      return [];
  }
};

const rotate = ([x, y]: Pt, [cx, cy]: Pt, deg: number): Pt => {
  const r = (deg * Math.PI) / 180;
  return [cx + (x - cx) * Math.cos(r) - (y - cy) * Math.sin(r), cy + (x - cx) * Math.sin(r) + (y - cy) * Math.cos(r)];
};

const wigBack = (k: Cutter, look: PersonLook): Shape[] =>
  look.hat === "wig" ? [{ d: k.path([[68, 40], [132, 40], [138, 84], [62, 84]]), fill: "#ddd6c8", shadow: true }] : [];

const build = (look: PersonLook, accent: AccentColor) => {
  const k = new Cutter(`person-${look.hair}-${look.hat}-${look.outfit}`, 0.45);
  const hidden = HIDES_HAIR_TOP.includes(look.hat);
  const skin = SKIN_TONES[look.skin];
  return {
    body: outfitShapes(k, look, accent),
    back: [...wigBack(k, look), ...(look.hat === "wig" ? [] : backHair(k, look, hidden))],
    neck: { d: k.path([[88, 60], [112, 60], [114, 82], [86, 82]]), fill: skin, shadow: true } as Shape,
    head: { d: k.path(ring(HEAD.cx, HEAD.cy, HEAD.rx, HEAD.ry, 0, 360, 30), 0.3), fill: skin, shadow: true } as Shape,
    facial: facialShapes(k, look),
    front: look.hat === "wig" ? [] : frontHair(k, look, hidden),
    hat: hatShapes(k, look, accent),
  };
};

const Layer: React.FC<{ shape: Shape }> = ({ shape }) => (
  <>
    {shape.shadow === false ? null : <path d={shape.d} fill={shade} transform="translate(1.6 2.2)" />}
    <path d={shape.d} fill={shape.fill} />
  </>
);

export type PersonBustProps = {
  width: number;
  initials: string;
  badge: string;
  badgeInk: string;
  look?: PersonLook;
  accent?: AccentColor;
  seed?: string;
};

export const bustHeight = (width: number): number => (width * BUST_VIEW.h) / BUST_VIEW.w;

export const PersonBust: React.FC<PersonBustProps> = ({ width, initials, badge, badgeInk, look = NEUTRAL_LOOK, accent = "red", seed = "person" }) => {
  const frame = useCurrentFrame();
  const chest = breath(frame + 11);
  const blink = isBlinking(seed, frame);
  const beat = useBeat(14);
  const nod = beat ? 7 * Math.sin(beat.t * Math.PI * 2) * (1 - beat.t) : 0;
  const tilt = 1.8 * Math.sin((frame / 30) * 0.8) + nod;
  const shift = beat ? (beat.index % 2 ? -2.4 : 2.4) * beat.wave : 0;
  const parts = React.useMemo(() => build(look, accent), [look, accent]);
  const featureInk = look.skin === "dark" || look.skin === "brown" ? "#120e0a" : colors.ink;
  const faceFill = SKIN_TONES[look.skin];
  return (
    <svg
      width={width}
      height={bustHeight(width)}
      viewBox={`${BUST_VIEW.x} ${BUST_VIEW.y} ${BUST_VIEW.w} ${BUST_VIEW.h}`}
      style={{ display: "block", overflow: "visible" }}
    >
      <g transform={`translate(0 128) scale(1 ${chest}) translate(0 -128)`}>
        {parts.body.map((s, i) => (
          <Layer key={`b-${i}`} shape={s} />
        ))}
        <g transform="translate(140 104) rotate(-6)">
          <circle cx={1.6} cy={2.2} r={16} fill={shade} />
          <circle r={16} fill={badge} />
          <text textAnchor="middle" dominantBaseline="central" fontFamily={fonts.text} fontWeight={800} fontSize={initials.length > 1 ? 14 : 18} fill={badgeInk} letterSpacing={-0.5}>
            {initials}
          </text>
        </g>
      </g>
      <g transform={`translate(0 ${(1 - chest) * 40}) rotate(${tilt} 100 70)`}>
        {parts.back.map((s, i) => (
          <Layer key={`k-${i}`} shape={s} />
        ))}
        <Layer shape={parts.neck} />
        <Layer shape={parts.head} />
        {blink ? (
          <>
            <rect x={84} y={44} width={9} height={2.2} fill={featureInk} />
            <rect x={107} y={44} width={9} height={2.2} fill={featureInk} />
          </>
        ) : (
          <>
            <circle cx={88.5 + shift} cy={45} r={3.3} fill={featureInk} />
            <circle cx={111.5 + shift} cy={45} r={3.3} fill={featureInk} />
          </>
        )}
        {parts.facial.map((s, i) => (
          <Layer key={`f-${i}`} shape={s} />
        ))}
        {look.facial === "beard" || look.facial === "goatee" ? <rect x={92} y={61} width={16} height={4} fill={faceFill} /> : null}
        <rect x={93} y={61.5} width={14} height={2.6} fill={featureInk} transform="rotate(-2 100 62)" />
        {parts.front.map((s, i) => (
          <Layer key={`h-${i}`} shape={s} />
        ))}
        {look.glasses ? (
          <g fill="none" stroke={colors.ink} strokeWidth={3}>
            <circle cx={88.5} cy={45} r={8.5} />
            <circle cx={111.5} cy={45} r={8.5} />
            <path d="M97 44 L103 44 M80 43 L68 40 M120 43 L132 40" />
          </g>
        ) : null}
        {parts.hat.map((s, i) => (
          <Layer key={`t-${i}`} shape={s} />
        ))}
      </g>
    </svg>
  );
};
