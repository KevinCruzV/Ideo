import { Cutter, oval, Piece } from "./cut";

export const PICTOS = [
  "globe",
  "flag",
  "pin",
  "city",
  "house",
  "factory",
  "bank",
  "coin",
  "chart-up",
  "chart-down",
  "ship",
  "plane",
  "train",
  "rocket",
  "satellite",
  "tank",
  "shield",
  "sword",
  "bomb",
  "dove",
  "handshake",
  "justice",
  "wall",
  "chain",
  "lock",
  "key",
  "crown",
  "ballot",
  "megaphone",
  "newspaper",
  "tv",
  "phone",
  "computer",
  "chip",
  "book",
  "brain",
  "heart",
  "eye",
  "clock",
  "calendar",
  "lightbulb",
  "atom",
  "flask",
  "leaf",
  "sun",
  "drop",
  "fire",
  "lightning",
  "mountain",
  "barrel",
  "gear",
  "people",
] as const;

export type PictoName = (typeof PICTOS)[number];

type Draw = (k: Cutter) => Piece[];

const bust = (k: Cutter, cx: number, top: number, scale: number, body: Piece["c"], head: Piece["c"]): Piece[] => {
  const w = 30 * scale;
  const h = 26 * scale;
  return [
    k.poly(
      [
        [cx - w * 0.62, top + h * 0.28],
        [cx - w * 0.28, top],
        [cx + w * 0.28, top],
        [cx + w * 0.62, top + h * 0.28],
        [cx + w * 0.7, top + h],
        [cx - w * 0.7, top + h],
      ],
      body,
    ),
    k.circle(cx, top - 11 * scale, 10.5 * scale, head),
  ];
};

const DRAW: Record<PictoName, Draw> = {
  globe: (k) => [
    k.circle(50, 50, 41, "blue"),
    k.poly([[20, 30], [34, 20], [46, 24], [48, 36], [40, 44], [36, 58], [28, 66], [22, 56], [14, 46]], "yellow"),
    k.poly([[56, 50], [70, 44], [82, 52], [84, 64], [74, 78], [62, 82], [58, 70], [52, 62]], "yellow"),
    k.poly([[58, 16], [70, 14], [78, 24], [68, 30], [60, 26]], "yellow"),
  ],
  flag: (k) => [
    k.rect(18, 8, 7, 82, "ink"),
    k.poly([[25, 12], [44, 8], [62, 14], [86, 10], [86, 46], [64, 50], [44, 44], [25, 48]], "red"),
    k.poly([[25, 30], [44, 26], [62, 32], [86, 28], [86, 46], [64, 50], [44, 44], [25, 48]], "yellow"),
    k.rect(8, 86, 28, 8, "ink"),
  ],
  pin: (k) => [
    k.oval(50, 90, 18, 4.5, "ink"),
    k.poly([[29, 48], [71, 48], [50, 88]], "red"),
    k.circle(50, 38, 27, "red"),
    k.circle(50, 38, 11, "cream"),
  ],
  city: (k) => [
    k.rect(10, 34, 22, 58, "blue"),
    k.rect(34, 12, 22, 80, "yellow"),
    k.rect(58, 40, 18, 52, "red"),
    k.rect(78, 56, 14, 36, "ink"),
    k.rect(15, 42, 5, 6, "cream"),
    k.rect(23, 42, 5, 6, "cream"),
    k.rect(15, 56, 5, 6, "cream"),
    k.rect(23, 56, 5, 6, "cream"),
    k.rect(15, 70, 5, 6, "cream"),
    k.rect(23, 70, 5, 6, "cream"),
    k.rect(39, 20, 5, 7, "ink"),
    k.rect(47, 20, 5, 7, "ink"),
    k.rect(39, 34, 5, 7, "ink"),
    k.rect(47, 34, 5, 7, "ink"),
    k.rect(39, 48, 5, 7, "ink"),
    k.rect(47, 48, 5, 7, "ink"),
    k.rect(62, 48, 4, 6, "cream"),
    k.rect(69, 48, 4, 6, "cream"),
    k.rect(62, 62, 4, 6, "cream"),
    k.rect(69, 62, 4, 6, "cream"),
  ],
  house: (k) => [
    k.rect(64, 18, 9, 22, "ink"),
    k.rect(20, 46, 60, 44, "yellow"),
    k.poly([[10, 50], [50, 14], [90, 50]], "red"),
    k.rect(43, 62, 15, 28, "blue"),
    k.rect(25, 57, 12, 12, "ink"),
    k.rect(64, 57, 12, 12, "ink"),
  ],
  factory: (k) => [
    k.rect(64, 10, 10, 44, "ink"),
    k.rect(78, 20, 9, 34, "ink"),
    k.circle(70, 6, 5, "cream"),
    k.poly([[10, 90], [10, 52], [32, 38], [32, 52], [54, 38], [54, 52], [90, 52], [90, 90]], "blue"),
    k.rect(17, 62, 10, 10, "yellow"),
    k.rect(35, 62, 10, 10, "yellow"),
    k.rect(53, 62, 10, 10, "yellow"),
    k.rect(71, 62, 10, 10, "yellow"),
    k.rect(42, 78, 16, 12, "red"),
  ],
  bank: (k) => [
    k.rect(8, 84, 84, 9, "ink"),
    k.rect(17, 40, 10, 42, "yellow"),
    k.rect(35, 40, 10, 42, "yellow"),
    k.rect(55, 40, 10, 42, "yellow"),
    k.rect(73, 40, 10, 42, "yellow"),
    k.rect(11, 32, 78, 8, "blue"),
    k.poly([[8, 34], [50, 8], [92, 34]], "red"),
    k.circle(50, 25, 5, "cream"),
  ],
  coin: (k) => [
    k.oval(30, 82, 24, 8, "ink"),
    k.oval(30, 78, 24, 8, "yellow"),
    k.oval(30, 70, 24, 8, "ink"),
    k.oval(30, 66, 24, 8, "yellow"),
    k.oval(30, 58, 24, 8, "ink"),
    k.oval(30, 54, 24, 8, "yellow"),
    k.circle(62, 46, 33, "yellow"),
    k.ring(62, 46, 26, 26, 3.5, "ink"),
    k.poly(
      [
        ...Array.from({ length: 15 }, (_, i) => {
          const a = ((45 + (270 * i) / 14) * Math.PI) / 180;
          return [62 + 16 * Math.cos(a), 46 + 16 * Math.sin(a)] as [number, number];
        }),
        ...Array.from({ length: 15 }, (_, i) => {
          const a = ((315 - (270 * i) / 14) * Math.PI) / 180;
          return [62 + 10 * Math.cos(a), 46 + 10 * Math.sin(a)] as [number, number];
        }),
      ],
      "ink",
    ),
    k.rect(42, 40, 20, 4.5, "ink"),
    k.rect(42, 48, 20, 4.5, "ink"),
  ],

  "chart-up": (k) => [
    k.rect(10, 10, 6, 82, "ink"),
    k.rect(10, 86, 82, 6, "ink"),
    k.rect(24, 64, 13, 22, "blue"),
    k.rect(43, 50, 13, 36, "yellow"),
    k.rect(62, 32, 13, 54, "red"),
    k.arrow(22, 52, 84, 12, 7, 18, "ink"),
  ],
  "chart-down": (k) => [
    k.rect(10, 10, 6, 82, "ink"),
    k.rect(10, 86, 82, 6, "ink"),
    k.rect(24, 32, 13, 54, "blue"),
    k.rect(43, 50, 13, 36, "yellow"),
    k.rect(62, 66, 13, 20, "red"),
    k.arrow(22, 16, 84, 60, 7, 18, "ink"),
  ],
  ship: (k) => [
    k.rect(52, 20, 11, 26, "ink"),
    k.rect(52, 26, 11, 5, "red"),
    k.rect(28, 40, 42, 18, "yellow"),
    k.rect(33, 45, 6, 6, "ink"),
    k.rect(44, 45, 6, 6, "ink"),
    k.rect(55, 45, 6, 6, "ink"),
    k.poly([[6, 56], [94, 56], [80, 80], [18, 80]], "red"),
    k.poly([[0, 80], [12, 75], [25, 80], [37, 75], [50, 80], [62, 75], [75, 80], [87, 75], [100, 80], [100, 94], [0, 94]], "blue"),
  ],
  plane: (k) => [
    k.poly([[10, 54], [46, 36], [54, 36], [90, 54], [90, 61], [54, 54], [46, 54], [10, 61]], "blue", 38),
    k.poly([[33, 86], [46, 77], [54, 77], [67, 86], [67, 91], [33, 91]], "blue", 38),
    k.poly([[50, 5], [56, 16], [57, 84], [50, 94], [43, 84], [44, 16]], "red", 38),
    k.poly([[47, 14], [53, 14], [54, 24], [46, 24]], "cream", 38),
  ],
  train: (k) => [
    k.rect(10, 88, 80, 6, "ink"),
    k.rect(27, 76, 11, 13, "ink"),
    k.rect(62, 76, 11, 13, "ink"),
    k.poly([[30, 10], [70, 10], [80, 22], [80, 80], [20, 80], [20, 22]], "blue"),
    k.rect(28, 20, 44, 24, "cream"),
    k.rect(20, 50, 60, 7, "red"),
    k.circle(33, 68, 6, "yellow"),
    k.circle(67, 68, 6, "yellow"),
  ],
  rocket: (k) => [
    k.poly([[40, 70], [60, 70], [57, 86], [50, 98], [43, 86]], "yellow", 24),
    k.poly([[45, 70], [55, 70], [50, 86]], "red", 24),
    k.poly([[36, 46], [20, 72], [36, 68]], "red", 24),
    k.poly([[64, 46], [80, 72], [64, 68]], "red", 24),
    k.poly([[50, 4], [64, 24], [65, 70], [35, 70], [36, 24]], "blue", 24),
    k.circle(54, 33, 9, "cream"),
    k.circle(54, 33, 5, "yellow"),
  ],
  satellite: (k) => [
    k.rect(2, 38, 34, 22, "blue", -24, 50, 50),
    k.rect(64, 38, 34, 22, "blue", -24, 50, 50),
    k.rect(13, 38, 2.6, 22, "cream", -24, 50, 50),
    k.rect(24, 38, 2.6, 22, "cream", -24, 50, 50),
    k.rect(75, 38, 2.6, 22, "cream", -24, 50, 50),
    k.rect(86, 38, 2.6, 22, "cream", -24, 50, 50),
    k.rect(34, 47, 32, 4, "ink", -24, 50, 50),
    k.rect(40, 34, 20, 32, "yellow", -24, 50, 50),
    k.rect(40, 60, 20, 6, "red", -24, 50, 50),
    k.bar(46, 32, 40, 20, 3, "ink"),
    k.arc(37, 17, 11, 180, 360, "red"),
    k.circle(37, 12, 3, "ink"),
  ],

  tank: (k) => [
    k.rect(58, 49, 36, 7, "ink"),
    k.poly([[30, 42], [62, 42], [69, 60], [24, 60]], "blue"),
    k.poly([[8, 58], [92, 58], [87, 70], [13, 70]], "blue"),
    k.rect(10, 68, 80, 18, "ink"),
    k.circle(22, 77, 6, "yellow"),
    k.circle(39, 77, 6, "yellow"),
    k.circle(56, 77, 6, "yellow"),
    k.circle(73, 77, 6, "yellow"),
  ],
  shield: (k) => [
    k.poly([[14, 14], [50, 5], [86, 14], [84, 54], [50, 95], [16, 54]], "blue"),
    k.poly([[50, 5], [86, 14], [84, 54], [50, 95]], "red"),
    k.poly([[24, 38], [50, 56], [76, 38], [76, 50], [50, 68], [24, 50]], "yellow"),
  ],
  sword: (k) => [
    k.poly([[50, 3], [57, 14], [57, 64], [43, 64], [43, 14]], "blue", 40),
    k.rect(48.5, 14, 3, 48, "cream", 40, 50, 50),
    k.rect(28, 63, 44, 8, "yellow", 40, 50, 50),
    k.rect(45.5, 71, 9, 18, "ink", 40, 50, 50),
    k.poly([[44, 89], [56, 89], [56, 97], [44, 97]], "yellow", 40),
  ],
  bomb: (k) => [
    k.rect(54, 22, 16, 14, "ink", 35),
    k.bar(66, 24, 76, 14, 3.5, "ink"),
    k.star(80, 12, 11, 4.5, 6, "yellow"),
    k.star(80, 12, 5, 2, 6, "red"),
    k.circle(44, 60, 33, "ink"),
    k.circle(32, 48, 7, "cream"),
  ],
  dove: (k) => [
    k.circle(50, 52, 42, "blue"),
    k.poly([[20, 60], [36, 48], [60, 48], [74, 38], [82, 40], [74, 54], [62, 66], [40, 70], [26, 70], [14, 76]], "cream"),
    k.poly([[38, 52], [44, 24], [60, 18], [62, 34], [56, 50]], "cream"),
    k.circle(77, 40, 7, "cream"),
    k.poly([[82, 37], [93, 41], [82, 44]], "yellow"),
    k.circle(78, 39, 1.8, "ink"),
    k.oval(90, 50, 5, 2.6, "yellow", 30),
    k.oval(86, 56, 5, 2.6, "yellow", -20),
  ],
  handshake: (k) => [
    k.bar(4, 96, 34, 62, 28, "blue"),
    k.bar(96, 96, 66, 62, 28, "red"),
    k.bar(26, 72, 36, 61, 30, "cream"),
    k.bar(74, 72, 64, 61, 30, "cream"),
    k.poly([[30, 62], [34, 42], [50, 30], [68, 34], [74, 50], [68, 64], [50, 70]], "yellow"),
    k.oval(40, 36, 12, 7, "yellow", -35),
    k.bar(48, 40, 62, 50, 4, "ink"),
    k.bar(46, 48, 60, 58, 4, "ink"),
    k.bar(44, 56, 56, 64, 4, "ink"),
    k.bar(33, 40, 46, 31, 3, "ink"),
  ],



  justice: (k) => [
    k.rect(30, 86, 40, 7, "ink"),
    k.rect(46.5, 14, 7, 74, "ink"),
    k.rect(10, 20, 80, 6, "ink"),
    k.poly([[22, 26], [10, 54], [34, 54]], "red"),
    k.poly([[78, 26], [66, 54], [90, 54]], "red"),
    k.arc(22, 54, 15, 0, 180, "yellow"),
    k.arc(78, 54, 15, 0, 180, "yellow"),
    k.circle(50, 14, 6, "yellow"),
  ],
  wall: (k) => [
    k.rect(8, 16, 26, 15, "red"),
    k.rect(37, 16, 26, 15, "red"),
    k.rect(66, 16, 26, 15, "red"),
    k.rect(8, 34, 12, 15, "red"),
    k.rect(23, 34, 26, 15, "red"),
    k.rect(52, 34, 26, 15, "red"),
    k.rect(81, 34, 11, 15, "red"),
    k.rect(8, 52, 26, 15, "red"),
    k.rect(37, 52, 26, 15, "red"),
    k.rect(66, 52, 26, 15, "red"),
    k.rect(8, 70, 12, 15, "red"),
    k.rect(23, 70, 26, 15, "red"),
    k.rect(52, 70, 26, 15, "red"),
    k.rect(81, 70, 11, 15, "red"),
    k.rect(4, 86, 92, 7, "ink"),
  ],
  chain: (k) => [
    k.ring(27, 73, 22, 13, 8, "ink", -45),
    k.ring(73, 27, 22, 13, 8, "ink", -45),
    k.ring(50, 50, 22, 13, 8, "yellow", 45),
  ],

  lock: (k) => [
    k.ring(50, 38, 22, 24, 8, "ink"),
    k.rect(20, 46, 60, 46, "yellow"),
    k.circle(50, 64, 7, "ink"),
    k.poly([[46, 66], [54, 66], [56, 81], [44, 81]], "ink"),
  ],

  key: (k) => [
    k.holed(k.circle(27, 50, 20, "yellow"), [oval(27, 50, 8, 8, 18)]),
    k.rect(44, 45, 50, 10, "yellow"),
    k.rect(74, 55, 7, 13, "yellow"),
    k.rect(85, 55, 7, 9, "yellow"),
    k.circle(27, 50, 3, "red"),
  ],
  crown: (k) => [
    k.poly([[12, 76], [10, 30], [31, 52], [50, 22], [69, 52], [90, 30], [88, 76]], "yellow"),
    k.circle(10, 28, 5.5, "yellow"),
    k.circle(50, 19, 5.5, "yellow"),
    k.circle(90, 28, 5.5, "yellow"),
    k.rect(10, 72, 80, 14, "red"),
    k.circle(30, 79, 4, "cream"),
    k.circle(50, 79, 4, "blue"),
    k.circle(70, 79, 4, "cream"),
  ],
  ballot: (k) => [
    k.rect(36, 12, 28, 40, "cream", -8),
    k.poly([[42, 30], [48, 36], [60, 20], [63, 24], [48, 42], [39, 33]], "red", -8),
    k.rect(14, 48, 72, 44, "blue"),
    k.rect(30, 46, 40, 6, "ink"),
    k.rect(34, 64, 32, 12, "yellow"),
  ],
  megaphone: (k) => [
    k.rect(36, 56, 10, 22, "ink", 12),
    k.rect(14, 40, 18, 22, "blue"),
    k.poly([[30, 40], [76, 18], [76, 82], [30, 62]], "red"),
    k.oval(77, 50, 6, 32, "yellow"),
    k.bar(86, 30, 94, 24, 4, "ink"),
    k.bar(88, 50, 98, 50, 4, "ink"),
    k.bar(86, 70, 94, 76, 4, "ink"),
  ],
  newspaper: (k) => [
    k.rect(20, 22, 70, 66, "blue", 6),
    k.rect(10, 14, 70, 66, "cream", -3),
    k.rect(17, 21, 55, 9, "ink", -3, 45, 47),
    k.rect(17, 36, 24, 22, "red", -3, 45, 47),
    k.rect(46, 37, 26, 3.5, "ink", -3, 45, 47),
    k.rect(46, 45, 26, 3.5, "ink", -3, 45, 47),
    k.rect(46, 53, 26, 3.5, "ink", -3, 45, 47),
    k.rect(17, 63, 55, 3.5, "ink", -3, 45, 47),
    k.rect(17, 70, 55, 3.5, "ink", -3, 45, 47),
  ],
  tv: (k) => [
    k.bar(50, 26, 32, 6, 3.5, "ink"),
    k.bar(50, 26, 68, 8, 3.5, "ink"),
    k.rect(20, 80, 10, 10, "ink"),
    k.rect(70, 80, 10, 10, "ink"),
    k.rect(10, 24, 80, 58, "blue"),
    k.rect(17, 31, 56, 44, "yellow"),
    k.circle(81, 42, 4.5, "cream"),
    k.circle(81, 56, 4.5, "cream"),
    k.poly([[22, 62], [34, 48], [44, 58], [56, 42], [68, 62], [68, 70], [22, 70]], "red"),
  ],
  phone: (k) => [
    k.rect(28, 6, 44, 88, "ink"),
    k.rect(33, 14, 34, 66, "blue"),
    k.rect(37, 20, 11, 11, "yellow"),
    k.rect(52, 20, 11, 11, "red"),
    k.rect(37, 35, 11, 11, "cream"),
    k.rect(52, 35, 11, 11, "yellow"),
    k.circle(50, 87, 3.5, "cream"),
  ],
  computer: (k) => [
    k.rect(16, 18, 68, 48, "ink"),
    k.rect(21, 23, 58, 38, "blue"),
    k.rect(27, 29, 26, 18, "cream"),
    k.rect(45, 37, 28, 18, "red"),
    k.poly([[6, 70], [94, 70], [88, 82], [12, 82]], "yellow"),
    k.rect(40, 72, 20, 4, "ink"),
  ],
  chip: (k) => [
    ...[34, 46, 58].flatMap((p) => [
      k.rect(p, 16, 7, 14, "ink"),
      k.rect(p, 70, 7, 14, "ink"),
      k.rect(16, p, 14, 7, "ink"),
      k.rect(70, p, 14, 7, "ink"),
    ]),
    k.rect(26, 26, 48, 48, "blue"),
    k.rect(37, 37, 26, 26, "yellow"),
    k.circle(32, 32, 2.5, "cream"),
  ],
  book: (k) => [
    k.poly([[4, 22], [50, 30], [96, 22], [96, 82], [50, 90], [4, 82]], "red"),
    k.poly([[9, 24], [48, 31], [48, 82], [9, 76]], "cream"),
    k.poly([[52, 31], [91, 24], [91, 76], [52, 82]], "cream"),
    k.bar(15, 38, 42, 42, 3.2, "ink"),
    k.bar(15, 48, 42, 52, 3.2, "ink"),
    k.bar(15, 58, 42, 62, 3.2, "ink"),
    k.bar(58, 42, 85, 38, 3.2, "ink"),
    k.bar(58, 52, 85, 48, 3.2, "ink"),
    k.bar(58, 62, 85, 58, 3.2, "ink"),
  ],
  brain: (k) => [
    k.circle(22, 44, 13, "red"),
    k.circle(30, 28, 14, "red"),
    k.circle(30, 64, 14, "red"),
    k.circle(42, 74, 11, "red"),
    k.circle(43, 20, 12, "red"),
    k.oval(36, 48, 15, 30, "red"),
    k.circle(78, 44, 13, "red"),
    k.circle(70, 28, 14, "red"),
    k.circle(70, 64, 14, "red"),
    k.circle(58, 74, 11, "red"),
    k.circle(57, 20, 12, "red"),
    k.oval(64, 48, 15, 30, "red"),
    k.poly([[48.5, 10], [51.5, 10], [52, 86], [48, 86]], "ink"),
    k.poly([[18, 40], [26, 36], [30, 42], [38, 38], [39, 42], [31, 47], [26, 41], [19, 45]], "cream"),
    k.poly([[24, 60], [32, 56], [36, 62], [42, 58], [43, 62], [36, 67], [31, 61], [25, 64]], "cream"),
    k.poly([[82, 40], [74, 36], [70, 42], [62, 38], [61, 42], [69, 47], [74, 41], [81, 45]], "cream"),
    k.poly([[76, 60], [68, 56], [64, 62], [58, 58], [57, 62], [64, 67], [69, 61], [75, 64]], "cream"),
  ],


  heart: (k) => [
    k.circle(33, 38, 20, "red"),
    k.circle(67, 38, 20, "red"),
    k.poly([[14, 44], [50, 30], [86, 44], [50, 88]], "red"),
    k.circle(28, 32, 6, "cream"),
  ],
  eye: (k) => [
    k.poly([[4, 50], [20, 34], [38, 26], [62, 26], [80, 34], [96, 50], [80, 66], [62, 74], [38, 74], [20, 66]], "blue"),
    k.circle(50, 50, 20, "yellow"),
    k.circle(50, 50, 9.5, "ink"),
    k.circle(44, 44, 4, "cream"),
  ],
  clock: (k) => [
    k.circle(50, 50, 42, "red"),
    k.circle(50, 50, 33, "cream"),
    k.rect(47.5, 21, 5, 7, "ink"),
    k.rect(47.5, 72, 5, 7, "ink"),
    k.rect(21, 47.5, 7, 5, "ink"),
    k.rect(72, 47.5, 7, 5, "ink"),
    k.bar(50, 50, 50, 28, 5, "ink"),
    k.bar(50, 50, 66, 60, 5, "blue"),
    k.circle(50, 50, 5, "ink"),
  ],
  calendar: (k) => [
    k.rect(12, 20, 76, 70, "cream"),
    k.rect(12, 20, 76, 18, "red"),
    k.rect(28, 10, 7, 18, "ink"),
    k.rect(65, 10, 7, 18, "ink"),
    ...[0, 1, 2].flatMap((r) =>
      [0, 1, 2, 3].map((c) => k.rect(19 + c * 17, 45 + r * 14, 12, 9, r === 1 && c === 2 ? "red" : "blue")),
    ),
  ],
  lightbulb: (k) => [
    k.bar(50, 12, 50, 2, 4, "red"),
    k.bar(22, 26, 14, 18, 4, "red"),
    k.bar(78, 26, 86, 18, 4, "red"),
    k.poly([[38, 56], [62, 56], [59, 72], [41, 72]], "yellow"),
    k.circle(50, 42, 25, "yellow"),
    k.rect(40, 72, 20, 7, "blue"),
    k.rect(42, 81, 16, 7, "blue"),
    k.circle(41, 34, 6, "cream"),
  ],
  atom: (k) => [
    k.ring(50, 50, 44, 16, 6, "blue", 0),
    k.ring(50, 50, 44, 16, 6, "blue", 60),
    k.ring(50, 50, 44, 16, 6, "blue", 120),
    k.circle(50, 50, 10, "red"),
    k.circle(91, 46, 5, "yellow"),
  ],
  flask: (k) => [
    k.poly([[40, 12], [60, 12], [60, 38], [86, 88], [14, 88], [40, 38]], "blue"),
    k.poly([[29, 60], [71, 60], [80, 82], [20, 82]], "yellow"),
    k.rect(35, 8, 30, 7, "ink"),
    k.circle(44, 72, 4, "cream"),
    k.circle(56, 66, 3, "cream"),
    k.circle(54, 50, 3.5, "cream"),
    k.circle(48, 40, 2.5, "cream"),
  ],
  leaf: (k) => [
    k.bar(26, 76, 12, 92, 5, "ink"),
    k.poly([[22, 80], [18, 56], [26, 34], [46, 18], [74, 10], [90, 8], [88, 26], [80, 52], [62, 72], [40, 82]], "yellow"),
    k.bar(24, 78, 76, 22, 3.5, "red"),
    k.bar(40, 61, 40, 42, 3, "red"),
    k.bar(55, 46, 74, 46, 3, "red"),
  ],
  sun: (k) => [
    ...Array.from({ length: 10 }, (_, i) => {
      const a = (i / 10) * Math.PI * 2;
      const c = [50 + 40 * Math.cos(a), 50 + 40 * Math.sin(a)];
      const l = [50 + 27 * Math.cos(a - 0.2), 50 + 27 * Math.sin(a - 0.2)];
      const r = [50 + 27 * Math.cos(a + 0.2), 50 + 27 * Math.sin(a + 0.2)];
      return k.poly([c as [number, number], l as [number, number], r as [number, number]], "red");
    }),
    k.circle(50, 50, 25, "yellow"),
  ],
  drop: (k) => [
    k.poly([[50, 6], [70, 44], [30, 44]], "blue"),
    k.circle(50, 62, 27, "blue"),
    k.circle(40, 62, 6, "cream"),
  ],
  fire: (k) => [
    k.poly([[50, 4], [64, 26], [72, 18], [82, 46], [78, 74], [62, 92], [38, 92], [22, 76], [18, 52], [28, 32], [36, 42]], "red"),
    k.poly([[50, 36], [62, 56], [66, 74], [56, 88], [44, 88], [34, 74], [38, 56], [44, 60]], "yellow"),
  ],
  lightning: (k) => [
    k.poly([[60, 4], [22, 54], [46, 54], [36, 96], [80, 40], [56, 40], [72, 4]], "yellow"),
    k.poly([[60, 4], [72, 4], [56, 40], [48, 40]], "red"),
  ],
  mountain: (k) => [
    k.poly([[46, 90], [72, 40], [98, 90]], "red"),
    k.poly([[4, 90], [42, 16], [80, 90]], "blue"),
    k.poly([[42, 16], [54, 40], [47, 36], [41, 42], [34, 36], [30, 40]], "cream"),
    k.circle(84, 18, 8, "yellow"),
  ],
  barrel: (k) => [
    k.poly([[26, 12], [74, 12], [79, 50], [74, 90], [26, 90], [21, 50]], "blue"),
    k.oval(50, 12, 24, 5, "ink"),
    k.rect(21, 30, 58, 6, "ink"),
    k.rect(21, 66, 58, 6, "ink"),
    k.poly([[50, 40], [57, 52], [43, 52]], "yellow"),
    k.circle(50, 55, 7.5, "yellow"),
  ],
  gear: (k) => {
    const pts: [number, number][] = [];
    const teeth = 8;
    for (let i = 0; i < teeth; i++) {
      const base = (i / teeth) * Math.PI * 2;
      const w = (Math.PI * 2) / teeth;
      [
        [base - w * 0.5, 32],
        [base - w * 0.22, 32],
        [base - w * 0.16, 44],
        [base + w * 0.16, 44],
        [base + w * 0.22, 32],
      ].forEach(([a, r]) => pts.push([50 + r * Math.cos(a), 50 + r * Math.sin(a)]));
    }
    return [k.holed(k.poly(pts, "blue"), [oval(50, 50, 13, 13, 20)])];
  },
  people: (k) => [
    ...bust(k, 24, 60, 0.95, "blue", "ink"),
    ...bust(k, 76, 60, 0.95, "yellow", "ink"),
    ...bust(k, 50, 52, 1.25, "red", "ink"),
    k.rect(4, 84, 92, 8, "ink"),
  ],
};

const cache = new Map<string, Piece[]>();

export const isPicto = (value: unknown): value is PictoName =>
  typeof value === "string" && (PICTOS as readonly string[]).includes(value.trim().toLowerCase());

export const pictoName = (value: unknown): PictoName | null => (isPicto(value) ? (value.trim().toLowerCase() as PictoName) : null);

export const pictoPieces = (name: PictoName): Piece[] => {
  const hit = cache.get(name);
  if (hit) return hit;
  const pieces = DRAW[name](new Cutter(`picto-${name}`));
  cache.set(name, pieces);
  return pieces;
};
