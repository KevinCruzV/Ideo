import { BodyPart, BodyPose } from "./bodyOptions";

export type P = [number, number];

export type HeadView = "front" | "right" | "left" | "back";

export type Rig = {
  head: P;
  headView: HeadView;
  asleep: boolean;
  shoulders: [P, P];
  hips: [P, P];
  elbows: [P, P];
  hands: [P, P];
  knees: [P, P];
  feet: [P, P];
  torso: [number, number];
  topView: boolean;
  feetUp: boolean;
};

const mirror = (rig: Rig): Rig => {
  const m = ([x, y]: P): P => [400 - x, y];
  const pair = ([a, b]: [P, P]): [P, P] => [m(b), m(a)];
  return {
    ...rig,
    head: m(rig.head),
    headView: rig.headView === "right" ? "left" : rig.headView === "left" ? "right" : rig.headView,
    shoulders: pair(rig.shoulders),
    hips: pair(rig.hips),
    elbows: pair(rig.elbows),
    hands: pair(rig.hands),
    knees: pair(rig.knees),
    feet: pair(rig.feet),
  };
};

const SIDE_LEFT: Rig = {
  head: [206, 66],
  headView: "right",
  asleep: true,
  shoulders: [
    [194, 108],
    [206, 106],
  ],
  hips: [
    [192, 182],
    [202, 180],
  ],
  elbows: [
    [230, 124],
    [222, 136],
  ],
  hands: [
    [238, 104],
    [238, 158],
  ],
  knees: [
    [236, 218],
    [228, 228],
  ],
  feet: [
    [212, 262],
    [206, 272],
  ],
  torso: [30, 30],
  topView: true,
  feetUp: false,
};

export const RIGS: Record<BodyPose, Rig> = {
  standing: {
    head: [200, 62],
    headView: "front",
    asleep: false,
    shoulders: [
      [174, 104],
      [226, 104],
    ],
    hips: [
      [184, 176],
      [216, 176],
    ],
    elbows: [
      [164, 142],
      [236, 142],
    ],
    hands: [
      [160, 178],
      [240, 178],
    ],
    knees: [
      [186, 222],
      [214, 222],
    ],
    feet: [
      [184, 266],
      [216, 266],
    ],
    torso: [54, 44],
    topView: false,
    feetUp: false,
  },
  sitting: {
    head: [190, 78],
    headView: "right",
    asleep: false,
    shoulders: [
      [188, 118],
      [192, 118],
    ],
    hips: [
      [182, 188],
      [186, 188],
    ],
    elbows: [
      [206, 156],
      [210, 152],
    ],
    hands: [
      [238, 160],
      [242, 156],
    ],
    knees: [
      [236, 190],
      [240, 190],
    ],
    feet: [
      [238, 240],
      [244, 240],
    ],
    torso: [36, 36],
    topView: false,
    feetUp: false,
  },
  walking: {
    head: [202, 62],
    headView: "right",
    asleep: false,
    shoulders: [
      [200, 104],
      [202, 104],
    ],
    hips: [
      [198, 176],
      [200, 176],
    ],
    elbows: [
      [214, 140],
      [188, 140],
    ],
    hands: [
      [232, 166],
      [180, 172],
    ],
    knees: [
      [188, 222],
      [214, 220],
    ],
    feet: [
      [170, 260],
      [230, 262],
    ],
    torso: [36, 36],
    topView: false,
    feetUp: false,
  },
  running: {
    head: [220, 70],
    headView: "right",
    asleep: false,
    shoulders: [
      [210, 110],
      [212, 110],
    ],
    hips: [
      [194, 176],
      [196, 176],
    ],
    elbows: [
      [190, 140],
      [234, 136],
    ],
    hands: [
      [174, 120],
      [252, 112],
    ],
    knees: [
      [176, 214],
      [234, 196],
    ],
    feet: [
      [140, 230],
      [232, 244],
    ],
    torso: [36, 36],
    topView: false,
    feetUp: false,
  },
  "lying-back": {
    head: [200, 66],
    headView: "front",
    asleep: true,
    shoulders: [
      [172, 108],
      [228, 108],
    ],
    hips: [
      [182, 182],
      [218, 182],
    ],
    elbows: [
      [162, 146],
      [238, 146],
    ],
    hands: [
      [164, 184],
      [236, 184],
    ],
    knees: [
      [186, 230],
      [214, 230],
    ],
    feet: [
      [186, 276],
      [214, 276],
    ],
    torso: [56, 46],
    topView: true,
    feetUp: true,
  },
  "lying-starfish": {
    head: [200, 70],
    headView: "front",
    asleep: true,
    shoulders: [
      [172, 112],
      [228, 112],
    ],
    hips: [
      [182, 184],
      [218, 184],
    ],
    elbows: [
      [146, 86],
      [254, 86],
    ],
    hands: [
      [132, 50],
      [268, 50],
    ],
    knees: [
      [166, 228],
      [234, 228],
    ],
    feet: [
      [146, 272],
      [254, 272],
    ],
    torso: [56, 46],
    topView: true,
    feetUp: true,
  },
  "lying-side-left": SIDE_LEFT,
  "lying-side-right": mirror(SIDE_LEFT),
  "lying-fetal": {
    head: [222, 96],
    headView: "right",
    asleep: true,
    shoulders: [
      [196, 124],
      [204, 120],
    ],
    hips: [
      [180, 190],
      [186, 186],
    ],
    elbows: [
      [226, 150],
      [220, 160],
    ],
    hands: [
      [244, 130],
      [242, 172],
    ],
    knees: [
      [240, 196],
      [234, 206],
    ],
    feet: [
      [200, 238],
      [194, 246],
    ],
    torso: [32, 32],
    topView: true,
    feetUp: false,
  },
  "lying-stomach": {
    head: [200, 70],
    headView: "back",
    asleep: true,
    shoulders: [
      [172, 110],
      [228, 110],
    ],
    hips: [
      [182, 184],
      [218, 184],
    ],
    elbows: [
      [140, 112],
      [260, 112],
    ],
    hands: [
      [146, 68],
      [254, 68],
    ],
    knees: [
      [186, 232],
      [238, 222],
    ],
    feet: [
      [188, 278],
      [222, 264],
    ],
    torso: [56, 46],
    topView: true,
    feetUp: false,
  },
};

export const rigOf = (pose: BodyPose): Rig => RIGS[pose];

const mid = (a: P, b: P): P => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
const lerp = (a: P, b: P, t: number): P => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];

export type Anchor = { at: P; rx: number; ry: number };

export const anchorOf = (rig: Rig, part: BodyPart): Anchor => {
  const neck = mid(rig.shoulders[0], rig.shoulders[1]);
  const pelvis = mid(rig.hips[0], rig.hips[1]);
  const facing = rig.headView === "right" ? 1 : rig.headView === "left" ? -1 : 0;
  const heartSide = facing === 0 ? (rig.headView === "back" ? -1 : 1) : 0;
  const chest = lerp(neck, pelvis, 0.3);
  switch (part) {
    case "head":
      return { at: rig.head, rx: 34, ry: 34 };
    case "brain":
      return { at: [rig.head[0], rig.head[1] - 6], rx: 22, ry: 18 };
    case "neck":
      return { at: lerp(rig.head, neck, 0.78), rx: 14, ry: 12 };
    case "throat":
      return { at: [lerp(rig.head, neck, 0.8)[0] + facing * 8, lerp(rig.head, neck, 0.8)[1]], rx: 11, ry: 10 };
    case "shoulders":
      return { at: neck, rx: Math.max(20, Math.abs(rig.shoulders[1][0] - rig.shoulders[0][0]) / 2 + 12), ry: 14 };
    case "chest":
      return { at: chest, rx: 26, ry: 18 };
    case "heart":
      return { at: [chest[0] + heartSide * 11 + facing * 6, chest[1] + 4], rx: 13, ry: 13 };
    case "lungs":
      return { at: chest, rx: 24, ry: 20 };
    case "stomach":
      return { at: [lerp(neck, pelvis, 0.62)[0] + facing * 6, lerp(neck, pelvis, 0.62)[1]], rx: 16, ry: 14 };
    case "back":
      return { at: lerp(neck, pelvis, 0.5), rx: 24, ry: 30 };
    case "spine":
      return { at: lerp(neck, pelvis, 0.5), rx: 10, ry: 38 };
    case "hips":
      return { at: pelvis, rx: 26, ry: 14 };
    case "arms":
      return { at: mid(rig.elbows[0], rig.elbows[1]), rx: Math.abs(rig.elbows[1][0] - rig.elbows[0][0]) / 2 + 16, ry: 18 };
    case "hands":
      return { at: mid(rig.hands[0], rig.hands[1]), rx: Math.abs(rig.hands[1][0] - rig.hands[0][0]) / 2 + 14, ry: Math.abs(rig.hands[1][1] - rig.hands[0][1]) / 2 + 14 };
    case "knees":
      return { at: mid(rig.knees[0], rig.knees[1]), rx: Math.abs(rig.knees[1][0] - rig.knees[0][0]) / 2 + 14, ry: Math.abs(rig.knees[1][1] - rig.knees[0][1]) / 2 + 14 };
    case "legs": {
      const a = mid(rig.hips[0], rig.knees[0]);
      const b = mid(rig.hips[1], rig.knees[1]);
      return { at: mid(a, b), rx: Math.abs(b[0] - a[0]) / 2 + 18, ry: 30 };
    }
    case "feet":
      return { at: mid(rig.feet[0], rig.feet[1]), rx: Math.abs(rig.feet[1][0] - rig.feet[0][0]) / 2 + 16, ry: Math.abs(rig.feet[1][1] - rig.feet[0][1]) / 2 + 12 };
  }
};
