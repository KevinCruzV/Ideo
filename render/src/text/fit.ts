const PAD_EM = 0.6;

const WIDE = /[\u1100-\u115f\u2e80-\ua4cf\uac00-\ud7a3\uf900-\ufaff\ufe30-\ufe4f\uff00-\uff60\uffe0-\uffe6]/;

const charEm = (c: string): number => {
  if (c === " ") return 0.26;
  if (WIDE.test(c)) return 1;
  if ("iljfrt.,:;!'’|()".includes(c)) return 0.34;
  if ("mwMW".includes(c)) return 0.86;
  if (/[A-Z0-9]/.test(c)) return 0.66;
  if (/[«»?%&@#]/.test(c)) return 0.62;
  return 0.56;
};

export const textWidth = (text: string, size: number): number => {
  let em = 0;
  for (const c of text) em += charEm(c);
  return em * size;
};

const breakWord = (word: string, size: number, room: number): string[] => {
  const parts: string[] = [];
  let current = "";
  for (const c of word) {
    if (current && textWidth(`${current}${c}-`, size) > room) {
      parts.push(`${current}-`);
      current = c;
    } else current += c;
  }
  if (current) parts.push(current);
  return parts;
};

export const wrap = (text: string, size: number, maxWidth: number): string[] => {
  const room = maxWidth - PAD_EM * size;
  const lines: string[] = [];
  let current = "";
  for (const word of text.split(" ").filter((w) => w.length > 0)) {
    const candidate = current ? `${current} ${word}` : word;
    if (textWidth(candidate, size) <= room) {
      current = candidate;
      continue;
    }
    if (current) lines.push(current);
    current = word;
  }
  if (current) lines.push(current);
  return lines;
};

export type Fit = { size: number; lines: string[] };

const balance = (text: string, size: number, maxWidth: number, lines: string[]): string[] => {
  if (lines.length < 2) return lines;
  let low = PAD_EM * size;
  let high = maxWidth;
  let best = lines;
  for (let i = 0; i < 14; i++) {
    const mid = (low + high) / 2;
    const attempt = wrap(text, size, mid);
    const fits = attempt.length <= lines.length && attempt.every((l) => textWidth(l, size) <= mid - PAD_EM * size);
    if (fits) {
      best = attempt;
      high = mid;
    } else low = mid;
  }
  return best;
};

export type FitOptions = { maxWidth: number; maxLines: number; max: number; min: number };

export const fitText = (text: string, { maxWidth, maxLines, max, min }: FitOptions): Fit => {
  const clean = text.trim();
  if (!clean) return { size: max, lines: [] };
  const room = (size: number) => maxWidth - PAD_EM * size;
  for (let size = max; size >= min; size -= 2) {
    const lines = wrap(clean, size, maxWidth);
    if (lines.length <= maxLines && lines.every((l) => textWidth(l, size) <= room(size))) {
      return { size, lines: balance(clean, size, maxWidth, lines) };
    }
  }
  const size = min;
  const lines = wrap(clean, size, maxWidth).flatMap((l) =>
    textWidth(l, size) <= room(size) ? [l] : breakWord(l, size, room(size)),
  );
  if (lines.length <= maxLines) return { size, lines };
  const kept = lines.slice(0, maxLines);
  let last = kept[maxLines - 1];
  while (last.length > 1 && textWidth(`${last}…`, size) > room(size)) last = last.slice(0, -1);
  kept[maxLines - 1] = `${last.replace(/[\s,.;:-]+$/, "")}…`;
  return { size, lines: kept };
};

export type KeySplit = { before: string; key: string; after: string };

const bare = (w: string) => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, "");

export const splitKey = (text: string, keyword?: string): KeySplit => {
  const words = text.split(" ").filter((w) => w.length > 0);
  if (words.length === 0) return { before: "", key: "", after: "" };
  const wanted = keyword ? keyword.split(" ").map(bare).filter((w) => w.length > 0) : [];
  if (wanted.length > 0) {
    for (let i = 0; i + wanted.length <= words.length; i++) {
      if (wanted.every((w, j) => bare(words[i + j]) === w)) {
        return {
          before: words.slice(0, i).join(" "),
          key: words.slice(i, i + wanted.length).join(" "),
          after: words.slice(i + wanted.length).join(" "),
        };
      }
    }
  }
  let best = 0;
  words.forEach((w, i) => {
    if (bare(w).length >= bare(words[best]).length) best = i;
  });
  return { before: words.slice(0, best).join(" "), key: words[best], after: words.slice(best + 1).join(" ") };
};
