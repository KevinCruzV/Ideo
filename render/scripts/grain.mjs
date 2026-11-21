import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { deflateSync } from "node:zlib";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SIZE = 384;

let state = 20261121;
const rand = () => {
  state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
  return state / 4294967296;
};

const lattice = (cell) => {
  const n = SIZE / cell;
  const grid = Array.from({ length: n * n }, rand);
  const at = (x, y) => grid[((y % n) + n) % n * n + (((x % n) + n) % n)];
  const smooth = (t) => t * t * (3 - 2 * t);
  return (x, y) => {
    const gx = x / cell;
    const gy = y / cell;
    const x0 = Math.floor(gx);
    const y0 = Math.floor(gy);
    const tx = smooth(gx - x0);
    const ty = smooth(gy - y0);
    const top = at(x0, y0) * (1 - tx) + at(x0 + 1, y0) * tx;
    const bottom = at(x0, y0 + 1) * (1 - tx) + at(x0 + 1, y0 + 1) * tx;
    return top * (1 - ty) + bottom * ty;
  };
};

const broad = lattice(96);
const mid = lattice(24);
const values = new Float32Array(SIZE * SIZE);
for (let y = 0; y < SIZE; y++) {
  for (let x = 0; x < SIZE; x++) {
    values[y * SIZE + x] = rand() * 9 + broad(x, y) * 7 + mid(x, y) * 4;
  }
}

for (let f = 0; f < 140; f++) {
  let x = rand() * SIZE;
  let y = rand() * SIZE;
  const angle = rand() * Math.PI * 2;
  const length = 6 + rand() * 18;
  const depth = 5 + rand() * 7;
  for (let s = 0; s < length; s++) {
    const px = ((Math.round(x) % SIZE) + SIZE) % SIZE;
    const py = ((Math.round(y) % SIZE) + SIZE) % SIZE;
    values[py * SIZE + px] += depth;
    x += Math.cos(angle + (rand() - 0.5) * 0.6);
    y += Math.sin(angle + (rand() - 0.5) * 0.6);
  }
}

const raw = Buffer.alloc((SIZE + 1) * SIZE);
for (let y = 0; y < SIZE; y++) {
  raw[y * (SIZE + 1)] = 0;
  for (let x = 0; x < SIZE; x++) {
    raw[y * (SIZE + 1) + 1 + x] = Math.max(0, Math.min(255, Math.round(255 - values[y * SIZE + x])));
  }
}

const table = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});
const crc = (buf) => {
  let c = 0xffffffff;
  for (const b of buf) c = table[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const sum = Buffer.alloc(4);
  sum.writeUInt32BE(crc(body));
  return Buffer.concat([len, body, sum]);
};

const header = Buffer.alloc(13);
header.writeUInt32BE(SIZE, 0);
header.writeUInt32BE(SIZE, 4);
header[8] = 8;
header[9] = 0;
const png = Buffer.concat([
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
  chunk("IHDR", header),
  chunk("IDAT", deflateSync(raw, { level: 9 })),
  chunk("IEND", Buffer.alloc(0)),
]);
const out = path.join(root, "public/grain.png");
writeFileSync(out, png);
console.log(path.relative(root, out), png.length);
