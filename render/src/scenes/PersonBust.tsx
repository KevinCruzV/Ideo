import React from "react";
import { useCurrentFrame } from "remotion";
import { Cutter, Pt } from "../pictos/cut";
import { breath, isBlinking } from "../mascot/pose";
import { useBeat } from "./beats";
import { AccentColor, colors, fonts, shade } from "../theme";
import { HAIR_TONES, HIDES_HAIR_TOP, NEUTRAL_LOOK, PersonLook, SKIN_TONES } from "./personLook";

export type View = { x: number; y: number; w: number; h: number };

export const BUST_VIEW: View = { x: 0, y: -46, w: 200, h: 174 };
export const CLOSE_VIEW: View = { x: 30, y: -48, w: 140, h: 164 };

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
    case "police":
      return [
        body("#243a6b"),
        { d: k.path([[82, 77], [118, 77], [100, 106]]), fill: "#c4d8ee" },
        { d: k.path([[96, 84], [104, 84], [106, 112], [100, 118], [94, 112]]), fill: colors.ink },
        { d: k.path([[80, 77], [100, 106], [90, 118], [68, 82]]), fill: "#243a6b", shadow: true },
        { d: k.path([[120, 77], [132, 82], [110, 118], [100, 106]]), fill: "#243a6b", shadow: true },
        { d: k.path([[30, 94], [58, 83], [63, 91], [35, 103]]), fill: colors.yellow, shadow: true },
        { d: k.path([[170, 94], [142, 83], [137, 91], [165, 103]]), fill: colors.yellow, shadow: true },
        { d: k.path([[121, 92], [140, 92], [140, 104], [130.5, 112], [121, 104]]), fill: colors.yellow, shadow: true },
        { d: k.path(ring(130.5, 101, 3.2, 3.2, 0, 360, 8)), fill: colors.red },
      ];
    case "firefighter":
      return [
        body("#c93a22"),
        { d: k.path([[72, 80], [128, 80], [126, 90], [74, 90]]), fill: colors.ink, shadow: true },
        { d: k.path([[20, 100], [180, 100], [181, 108], [19, 108]]), fill: colors.yellow },
        { d: k.path([[18, 114], [182, 114], [183, 122], [17, 122]]), fill: colors.yellow },
        { d: k.path([[98, 90], [102, 90], [102, 128], [98, 128]]), fill: colors.ink },
        ...[93, 107].map((y) => ({ d: k.path(ring(88, y, 3, 3, 0, 360, 8)), fill: colors.cream })),
      ];
    case "doctor":
      return [
        body(colors.cream),
        { d: k.path([[84, 77], [116, 77], [100, 104]]), fill: "#34a0ab" },
        { d: k.path([[80, 77], [100, 104], [92, 126], [66, 82]]), fill: colors.cream, shadow: true },
        { d: k.path([[120, 77], [134, 82], [108, 126], [100, 104]]), fill: colors.cream, shadow: true },
        { d: k.path(ring(100, 80, 26, 34, 18, 162, 20).concat(ring(100, 80, 21, 29, 162, 18, 20))), fill: colors.ink, shadow: true },
        { d: k.path(ring(104, 112, 6, 6, 0, 360, 10)), fill: "#bfc4c9", shadow: true },
        { d: k.path(ring(104, 112, 2.6, 2.6, 0, 360, 8)), fill: colors.ink },
      ];
    case "judge":
      return [
        body("#17151b"),
        { d: k.path([[78, 77], [122, 77], [112, 96], [100, 112], [88, 96]]), fill: colors.cream, shadow: true },
        { d: k.path([[78, 77], [100, 112], [88, 128], [64, 82]]), fill: "#17151b", shadow: true },
        { d: k.path([[122, 77], [136, 82], [112, 128], [100, 112]]), fill: "#17151b", shadow: true },
        { d: k.path([[64, 82], [70, 80], [94, 128], [88, 128]]), fill: colors.red },
        { d: k.path([[136, 82], [130, 80], [106, 128], [112, 128]]), fill: colors.red },
        { d: k.path([[20, 120], [180, 120], [181, 126], [19, 126]]), fill: colors.red },
      ];
    case "soldier":
      return [
        body("#5b6340"),
        { d: k.path(ring(52, 100, 14, 9, 0, 360, 10)), fill: "#3f452c" },
        { d: k.path(ring(150, 108, 16, 10, 0, 360, 10)), fill: "#79845a" },
        { d: k.path(ring(40, 118, 12, 8, 0, 360, 10)), fill: "#79845a" },
        { d: k.path([[82, 77], [118, 77], [100, 100]]), fill: "#c9ba8c" },
        { d: k.path([[80, 77], [100, 100], [92, 110], [66, 82]]), fill: "#5b6340", shadow: true },
        { d: k.path([[120, 77], [134, 82], [108, 110], [100, 100]]), fill: "#5b6340", shadow: true },
        { d: k.path([[126, 96], [152, 96], [152, 104], [126, 104]]), fill: colors.cream },
        { d: k.path([[88, 88], [92, 86], [100, 106], [96, 108]]), fill: "#bfc4c9" },
        { d: k.path(ring(98, 108, 4, 5, 0, 360, 8)), fill: "#bfc4c9", shadow: true },
      ];
    case "worker":
      return [
        body(colors.blue),
        { d: k.path([[84, 77], [116, 77], [100, 92]]), fill: colors.cream },
        { d: k.path([[58, 82], [84, 77], [100, 100], [116, 77], [142, 82], [138, 128], [62, 128]]), fill: "#ee7d1a", shadow: true },
        { d: k.path([[68, 82], [78, 80], [76, 128], [66, 128]]), fill: "#e9e4c8" },
        { d: k.path([[122, 80], [132, 82], [134, 128], [124, 128]]), fill: "#e9e4c8" },
        { d: k.path([[98, 100], [102, 100], [102, 128], [98, 128]]), fill: "#bf5f0f" },
      ];
    case "journalist":
      return [
        body("#a98558"),
        { d: k.path([[84, 77], [116, 77], [100, 96]]), fill: colors.cream },
        { d: k.path([[80, 77], [100, 96], [90, 112], [66, 82]]), fill: "#a98558", shadow: true },
        { d: k.path([[120, 77], [134, 82], [110, 112], [100, 96]]), fill: "#a98558", shadow: true },
        { d: k.path([[88, 80], [92, 80], [100, 106], [96, 108]]), fill: colors.ink },
        { d: k.path([[112, 80], [108, 80], [100, 106], [104, 108]]), fill: colors.ink },
        { d: k.path([[88, 106], [112, 106], [112, 126], [88, 126]]), fill: colors.cream, shadow: true },
        { d: k.path([[88, 106], [112, 106], [112, 112], [88, 112]]), fill: colors.red },
        { d: k.path([[128, 96], [160, 96], [160, 120], [128, 120]]), fill: colors.ink, shadow: true },
        { d: k.path(ring(144, 108, 7, 7, 0, 360, 10)), fill: colors.cream },
        { d: k.path(ring(144, 108, 3.4, 3.4, 0, 360, 8)), fill: "#3b352d" },
      ];
    case "lawyer":
      return [
        body("#2e3547"),
        ...[50, 64, 78, 122, 136, 150].map((x) => ({ d: k.path([[x, 90], [x + 2, 90], [x + 2, 128], [x, 128]]), fill: "rgba(251,246,234,.35)" })),
        { d: k.path([[82, 77], [118, 77], [100, 108]]), fill: colors.cream },
        { d: k.path([[96, 84], [104, 84], [107, 118], [100, 126], [93, 118]]), fill: colors.yellow },
        { d: k.path([[80, 77], [100, 108], [86, 126], [66, 82]]), fill: "#2e3547", shadow: true },
        { d: k.path([[120, 77], [134, 82], [114, 126], [100, 108]]), fill: "#2e3547", shadow: true },
        { d: k.path([[124, 98], [140, 98], [140, 106], [124, 106]]), fill: colors.cream },
        { d: k.path(ring(112, 98, 3.4, 3.4, 0, 360, 8)), fill: colors.yellow },
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
    case "police-cap":
      return [
        { d: k.path([[70, 26], [64, -4], [136, -4], [130, 26]]), fill: "#243a6b", shadow: true },
        { d: k.path([[56, -8], [144, -8], [134, 3], [66, 3]]), fill: "#33508f", shadow: true },
        { d: k.path([[69, 15], [131, 15], [131, 26], [69, 26]]), fill: colors.ink },
        { d: k.path([[72, 25], [128, 25], [140, 34], [60, 34]]), fill: colors.ink, shadow: true },
        { d: k.path(ring(100, 12, 5, 5.5, 0, 360, 8)), fill: colors.yellow },
      ];
    case "fire-helmet":
      return [
        { d: k.path([[44, 28], [156, 28], [164, 40], [36, 40]]), fill: "#a82a1c", shadow: true },
        { d: k.path(ring(100, 30, 41, 40, 180, 360, 22).concat([[141, 30], [59, 30]])), fill: "#d23a22", shadow: true },
        { d: k.path([[95, -12], [105, -12], [105, 30], [95, 30]]), fill: "#a82a1c" },
        { d: k.path([[84, 6], [116, 6], [116, 22], [100, 30], [84, 22]]), fill: colors.yellow, shadow: true },
        { d: k.path(ring(100, 16, 3.6, 3.6, 0, 360, 8)), fill: colors.ink },
      ];
    case "hard-hat":
      return [
        { d: k.path(ring(100, 30, 40, 38, 180, 360, 22).concat([[140, 30], [60, 30]])), fill: "#f0b92a", shadow: true },
        { d: k.path([[93, -8], [107, -8], [107, 30], [93, 30]]), fill: "#d19a14" },
        { d: k.path([[52, 26], [148, 26], [154, 34], [46, 34]]), fill: "#f0b92a", shadow: true },
        { d: k.path([[60, 26], [140, 26], [141, 29], [59, 29]]), fill: "#d19a14" },
      ];
    case "army-helmet":
      return [
        { d: k.path(ring(100, 30, 42, 38, 180, 360, 22).concat([[142, 30], [58, 30]])), fill: "#5b6340", shadow: true },
        { d: k.path(ring(78, 12, 9, 6, 0, 360, 10)), fill: "#3f452c" },
        { d: k.path(ring(118, 8, 11, 6, 0, 360, 10)), fill: "#79845a" },
        { d: k.path([[54, 24], [146, 24], [148, 32], [52, 32]]), fill: "#3f452c", shadow: true },
        { d: k.path([[60, 32], [66, 32], [68, 58], [62, 58]]), fill: colors.ink },
        { d: k.path([[134, 32], [140, 32], [138, 58], [132, 58]]), fill: colors.ink },
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
  const k = new Cutter(`person-${look.hair}-${look.hat}-${look.outfit}-${look.gender}-${look.age}`, 0.45);
  const hidden = HIDES_HAIR_TOP.includes(look.hat);
  const skin = SKIN_TONES[look.skin];
  return {
    body: outfitShapes(k, look, accent),
    back: [...wigBack(k, look), ...(look.hat === "wig" ? [] : backHair(k, look, hidden))],
    neck: {
      d: k.path(
        look.gender === "woman"
          ? [[91, 60], [109, 60], [110, 84], [90, 84]]
          : look.age === "child"
            ? [[89, 60], [111, 60], [113, 90], [87, 90]]
            : [[86, 60], [114, 60], [116, 82], [84, 82]],
      ),
      fill: skin,
      shadow: true,
    } as Shape,
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
  view?: View;
};

export const bustHeight = (width: number, view: View = BUST_VIEW): number => (width * view.h) / view.w;

export const PersonBust: React.FC<PersonBustProps> = ({ width, initials, badge, badgeInk, look = NEUTRAL_LOOK, accent = "red", seed = "person", view = BUST_VIEW }) => {
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
  const woman = look.gender === "woman";
  const child = look.age === "child";
  const old = look.age === "old";
  const hairInk = HAIR_TONES[look.hairColor];
  const bodyFit = child ? "translate(100 128) scale(.86) translate(-100 -128)" : woman ? "translate(100 128) scale(.9 1) translate(-100 -128)" : "";
  const headFit = child ? "translate(100 70) scale(1.12) translate(-100 -70)" : "";
  const eye = child ? 4.4 : 3.3;
  return (
    <svg
      width={width}
      height={bustHeight(width, view)}
      viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`}
      style={{ display: "block", overflow: "visible" }}
    >
      <g transform={`translate(0 128) scale(1 ${chest}) translate(0 -128)`}>
        <g transform={bodyFit}>
        {parts.body.map((s, i) => (
          <Layer key={`b-${i}`} shape={s} />
        ))}
        </g>
        <g transform="translate(140 104) rotate(-6)">
          <circle cx={1.6} cy={2.2} r={16} fill={shade} />
          <circle r={16} fill={badge} />
          <text textAnchor="middle" dominantBaseline="central" fontFamily={fonts.text} fontWeight={800} fontSize={initials.length > 1 ? 14 : 18} fill={badgeInk} letterSpacing={-0.5}>
            {initials}
          </text>
        </g>
      </g>
      <g transform={`translate(0 ${(1 - chest) * 40}) rotate(${tilt} 100 70) ${headFit}`}>
        {parts.back.map((s, i) => (
          <Layer key={`k-${i}`} shape={s} />
        ))}
        <Layer shape={parts.neck} />
        {[66, 134].map((x) => (
          <ellipse key={`ear-${x}`} cx={x} cy={46} rx={5.5} ry={8} fill={faceFill} stroke={shade} strokeWidth={0.8} />
        ))}
        {woman ? [66, 134].map((x) => <circle key={`ring-${x}`} cx={x} cy={57} r={3.6} fill={colors.yellow} stroke={shade} strokeWidth={0.6} />) : null}
        <Layer shape={parts.head} />
        <path d="M98 48 L102 48 L104 57 L96 57 Z" fill="rgba(31,26,20,.16)" />
        {child ? [[80, 54], [120, 54]].map(([cx, cy]) => <circle key={`cheek-${cx}`} cx={cx} cy={cy} r={5.4} fill="rgba(226,70,44,.3)" />) : null}
        {woman
          ? [[82, 94, 1], [118, 106, -1]].map(([a, b, d]) => (
              <path key={`brow-${a}`} d={`M${a} 39 Q${(a + b) / 2} ${36.4 - d * 0.4} ${b} ${38 + d * 0.6}`} fill="none" stroke={hairInk} strokeWidth={1.7} strokeLinecap="round" />
            ))
          : [[82, 94], [106, 118]].map(([a, b]) => (
              <path key={`brow-${a}`} d={`M${a} ${old ? 36.5 : 37.5} L${b} ${old ? 36.5 : 37.5} L${b} ${old ? 40.4 : 40} L${a} ${old ? 41 : 40.6} Z`} fill={hairInk} />
            ))}
        {old ? (
          <g fill="none" stroke="rgba(31,26,20,.34)" strokeWidth={1.1} strokeLinecap="round">
            <path d="M84 29 Q100 26 116 29 M86 33 Q100 30 114 33 M81 51 Q88 54 95 51 M105 51 Q112 54 119 51 M88 58 Q85 66 90 73 M112 58 Q115 66 110 73" />
          </g>
        ) : null}
        {blink ? (
          <>
            <rect x={84} y={44} width={9} height={2.2} fill={featureInk} />
            <rect x={107} y={44} width={9} height={2.2} fill={featureInk} />
          </>
        ) : (
          <>
            <circle cx={88.5 + shift} cy={45} r={eye} fill={featureInk} />
            <circle cx={111.5 + shift} cy={45} r={eye} fill={featureInk} />
            {child ? [[90, 43.6], [113, 43.6]].map(([cx, cy]) => <circle key={`glint-${cx}`} cx={cx + shift} cy={cy} r={1.3} fill={colors.cream} />) : null}
          </>
        )}
        {woman ? <path d="M83 41.5 L79 38.6 M85.4 40.2 L83.4 36.6 M117 41.5 L121 38.6 M114.6 40.2 L116.6 36.6" stroke={featureInk} strokeWidth={1.5} strokeLinecap="round" /> : null}
        {parts.facial.map((s, i) => (
          <Layer key={`f-${i}`} shape={s} />
        ))}
        {look.facial === "beard" || look.facial === "goatee" ? <rect x={92} y={61} width={16} height={4} fill={faceFill} /> : null}
        {woman ? (
          <path d="M92 61 Q96 58.4 100 59.6 Q104 58.4 108 61 Q100 67 92 61 Z" fill="#c4372c" />
        ) : (
          <rect x={93} y={61.5} width={14} height={2.6} fill={featureInk} transform="rotate(-2 100 62)" />
        )}
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
