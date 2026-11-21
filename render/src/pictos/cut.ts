import { signed } from "../paper/motion";

export type Ink = "red" | "yellow" | "blue" | "ink" | "cream";

export type Piece = { d: string; c: Ink };

export type Pt = [number, number];

const f = (v: number) => v.toFixed(2);

export class Cutter {
  private n = 0;

  constructor(private readonly seed: string, private readonly rough = 0.55) {}

  private j(max = this.rough): number {
    this.n += 1;
    return signed(`${this.seed}:${this.n}`, max);
  }

  private rotate(points: Pt[], deg: number, cx: number, cy: number): Pt[] {
    if (!deg) return points;
    const r = (deg * Math.PI) / 180;
    const cos = Math.cos(r);
    const sin = Math.sin(r);
    return points.map(([x, y]) => [cx + (x - cx) * cos - (y - cy) * sin, cy + (x - cx) * sin + (y - cy) * cos]);
  }

  path(points: Pt[], rough = this.rough): string {
    return `M${points.map(([x, y]) => `${f(x + this.j(rough))} ${f(y + this.j(rough))}`).join(" L")} Z`;
  }

  poly(points: Pt[], c: Ink, rot = 0, cx = 50, cy = 50): Piece {
    return { d: this.path(this.rotate(points, rot, cx, cy)), c };
  }

  rect(x: number, y: number, w: number, h: number, c: Ink, rot = 0, cx?: number, cy?: number): Piece {
    const pts: Pt[] = [
      [x, y],
      [x + w, y],
      [x + w, y + h],
      [x, y + h],
    ];
    return { d: this.path(this.rotate(pts, rot, cx ?? x + w / 2, cy ?? y + h / 2), Math.min(this.rough, Math.min(w, h) * 0.12)), c };
  }

  ovalPoints(cx: number, cy: number, rx: number, ry: number, rot = 0, from = 0, to = 360): Pt[] {
    const span = to - from;
    const count = Math.max(12, Math.min(44, Math.round(Math.max(rx, ry) * 1.1 * (span / 360) + 6)));
    const closed = span >= 360;
    const pts: Pt[] = Array.from({ length: closed ? count : count + 1 }, (_, i) => {
      const a = ((from + (span * i) / count) * Math.PI) / 180;
      const wob = 1 - Math.abs(this.j(0.012));
      return [cx + rx * wob * Math.cos(a), cy + ry * wob * Math.sin(a)];
    });
    return this.rotate(pts, rot, cx, cy);
  }

  circle(cx: number, cy: number, r: number, c: Ink): Piece {
    return { d: this.path(this.ovalPoints(cx, cy, r, r), 0.25), c };
  }

  oval(cx: number, cy: number, rx: number, ry: number, c: Ink, rot = 0): Piece {
    return { d: this.path(this.ovalPoints(cx, cy, rx, ry, rot), 0.25), c };
  }

  arc(cx: number, cy: number, r: number, from: number, to: number, c: Ink, extra: Pt[] = []): Piece {
    return { d: this.path([...this.ovalPoints(cx, cy, r, r, 0, from, to), ...extra], 0.25), c };
  }

  ring(cx: number, cy: number, rx: number, ry: number, thick: number, c: Ink, rot = 0): Piece {
    const outer = this.path(this.ovalPoints(cx, cy, rx, ry, rot), 0.2);
    const inner = this.path(this.ovalPoints(cx, cy, rx - thick, ry - thick, rot).reverse(), 0.2);
    return { d: `${outer} ${inner}`, c };
  }

  holed(outer: Piece, holes: Pt[][]): Piece {
    return { d: `${outer.d} ${holes.map((h) => this.path(h.slice().reverse(), 0.2)).join(" ")}`, c: outer.c };
  }

  star(cx: number, cy: number, ro: number, ri: number, n: number, c: Ink, rot = -90): Piece {
    const pts: Pt[] = Array.from({ length: n * 2 }, (_, i) => {
      const r = i % 2 === 0 ? ro : ri;
      const a = ((rot + (180 / n) * i) * Math.PI) / 180;
      return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
    });
    return this.poly(pts, c);
  }

  bar(x1: number, y1: number, x2: number, y2: number, thick: number, c: Ink): Piece {
    const len = Math.hypot(x2 - x1, y2 - y1);
    const deg = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
    const cx = (x1 + x2) / 2;
    const cy = (y1 + y2) / 2;
    return this.rect(cx - len / 2, cy - thick / 2, len, thick, c, deg, cx, cy);
  }

  arrow(x1: number, y1: number, x2: number, y2: number, thick: number, head: number, c: Ink): Piece {
    const len = Math.hypot(x2 - x1, y2 - y1);
    const deg = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
    const shaft = len - head;
    const pts: Pt[] = [
      [0, -thick / 2],
      [shaft, -thick / 2],
      [shaft, -head * 0.62],
      [len, 0],
      [shaft, head * 0.62],
      [shaft, thick / 2],
      [0, thick / 2],
    ];
    const moved: Pt[] = pts.map(([x, y]) => [x1 + x, y1 + y]);
    return this.poly(moved, c, deg, x1, y1);
  }
}

export const oval = (cx: number, cy: number, rx: number, ry: number, steps = 28): Pt[] =>
  Array.from({ length: steps }, (_, i) => {
    const a = (i / steps) * Math.PI * 2;
    return [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
  });
