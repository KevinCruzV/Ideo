import React from "react";
import { useCurrentFrame } from "remotion";
import { MAP_FOCUS, MapFocus } from "../map/codes";
import { COUNTRIES, VIEWS } from "../map/world";
import { cutEdge, entry, tween } from "../paper/motion";
import { PaperStrip, stripHeight } from "../paper/PaperStrip";
import { colors, shade } from "../theme";
import { fitText, textWidth } from "../text/fit";
import { useAccent } from "./accent";
import { useBeat } from "./beats";
import { list, str, strList } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { enterFor } from "./timing";

const LAND = "#ddd0b4";
const LAND_EDGE = "#f6efdf";
const SMALL_PX = 26;
const LABEL_MAX = 52;
const LABEL_MIN = 44;
const PIN = 30;
const TOP_ROOM = 150;

export const focusOf = (value: unknown): MapFocus => {
  const key = str(value).toLowerCase();
  return (MAP_FOCUS as readonly string[]).includes(key) ? (key as MapFocus) : "world";
};

type Place = { code: string; label: string };

export const placesOf = (value: unknown): Place[] =>
  list(value, 6).flatMap((p) => {
    const o = p && typeof p === "object" ? (p as Record<string, unknown>) : { code: p };
    const code = str(o.code).toLowerCase();
    return COUNTRIES[code] ? [{ code, label: str(o.label).slice(0, 24) }] : [];
  });

export const routeOf = (value: unknown): string[] =>
  strList(value, 6)
    .map((c) => c.toLowerCase())
    .filter((c) => COUNTRIES[c]);

type Box = { x: number; y: number; w: number; h: number };


export const MapScene: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const beat = useBeat();
  const focus = focusOf(props.focus);
  const places = placesOf(props.places);
  const route = routeOf(props.route);
  const top = areaTop(props);
  const area = areaFor(top + 10, BOX_L, BOX_W);
  const [fx, vy, fw, vh] = VIEWS[focus];
  const marks = [...places.map((p) => p.code), ...route].map((c) => COUNTRIES[c]);
  const target = BOX_W / Math.max(200, area.height - TOP_ROOM);
  const spanX0 = marks.length ? Math.min(...marks.map((c) => c.cx)) - fw * 0.1 : fx;
  const spanX1 = marks.length ? Math.max(...marks.map((c) => c.cx)) + fw * 0.1 : fx + fw;
  const vw = Math.min(fw, Math.max(spanX1 - spanX0, vh * target, marks.length <= 1 ? fw * 0.5 : 0));
  const vx = Math.max(fx, Math.min(fx + fw - vw, (spanX0 + spanX1) / 2 - vw / 2));
  const aspect = vw / vh;
  const mapH = Math.min(area.height - TOP_ROOM, BOX_W / aspect);
  const mapW = mapH * aspect;
  const scale = mapW / vw;
  const totalH = TOP_ROOM + mapH;
  const toPx = (x: number, y: number) => [(x - vx) * scale, (y - vy) * scale + TOP_ROOM] as const;
  const totalW = Math.max(mapW, Math.min(BOX_W, mapW + 40));
  const offsetX = (totalW - mapW) / 2;
  const edge = cutEdge(`map-${focus}`, 0.6);
  const sheet = entry(frame, -3, { dy: 50, spin: -3, from: 0.95 });

  const labelSize = Math.max(LABEL_MIN, Math.min(LABEL_MAX, ...places.map((p) => (p.label ? fitText(p.label, { maxWidth: 680, maxLines: 1, max: LABEL_MAX, min: LABEL_MIN }).size : LABEL_MAX))));
  const placed: Box[] = places.map((p) => {
    const c = COUNTRIES[p.code];
    const [px, py] = toPx(c.cx, c.cy);
    return { x: px + offsetX - PIN / 2 - 4, y: py - PIN * 1.6 - 4, w: PIN + 8, h: PIN * 1.6 + 8 };
  });
  const pins = places.map((p, i) => {
    const c = COUNTRIES[p.code];
    const [px, py] = toPx(c.cx, c.cy);
    const x = px + offsetX;
    const w = p.label ? textWidth(p.label, labelSize) + labelSize * 0.6 : 0;
    const h = stripHeight(labelSize);
    const ys = [py - PIN * 1.6 - h - 6, py + 12, py - PIN * 1.6 - h * 2 - 14, py + h + 20, py - PIN * 1.6 - h * 3 - 22, py + h * 2 + 28];
    const xs = [x - w / 2, x - w + PIN, x - PIN, x - w / 2 - w * 0.35, x - w / 2 + w * 0.35];
    let best = { left: Math.max(0, Math.min(totalW - w, x - w / 2)), ly: ys[0], cost: Infinity };
    for (const cy of ys) {
      for (const cx of xs) {
        const left0 = Math.max(0, Math.min(totalW - w, cx));
        if (cy < 0 || cy + h > totalH) continue;
        const box = { x: left0, y: cy, w, h };
        const cost = placed.reduce((sum, b) => {
          const ox = Math.min(b.x + b.w, box.x + box.w) - Math.max(b.x, box.x);
          const oy = Math.min(b.y + b.h, box.y + box.h) - Math.max(b.y, box.y);
          return sum + (ox > 0 && oy > 0 ? ox * oy : 0);
        }, 0) + Math.hypot(left0 + w / 2 - x, cy + h / 2 - py) * 0.5;
        if (cost < best.cost) best = { left: left0, ly: cy, cost };
      }
    }
    const left = best.left;
    const ly = best.ly;
    if (p.label) placed.push({ x: left, y: ly, w, h });
    return { ...p, x, y: py, left, ly, at: enterFor(`places.${i}`, items, from, to), small: c.size * scale < SMALL_PX };
  });

  const routeAt = items.some((i) => i.el === "route") ? enterFor("route", items, from, to) : Math.max(0, ...pins.map((p) => p.at)) + 8;
  const routePts = route.map((code) => {
    const c = COUNTRIES[code];
    return toPx(c.cx, c.cy);
  });
  const routeD = routePts
    .map(([x, y], i) => {
      if (i === 0) return `M${(x + offsetX).toFixed(1)} ${y.toFixed(1)}`;
      const [px, py] = routePts[i - 1];
      const mx = (px + x) / 2 + offsetX;
      const my = (py + y) / 2 - Math.hypot(x - px, y - py) * 0.18;
      return `Q${mx.toFixed(1)} ${my.toFixed(1)} ${(x + offsetX).toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
  const routeLen = routePts.reduce((sum, [x, y], i) => (i === 0 ? 0 : sum + Math.hypot(x - routePts[i - 1][0], y - routePts[i - 1][1]) * 1.1), 0);
  const routeDraw = tween(frame, routeAt, Math.max(24, Math.min(60, routeLen / 12)));
  const last = routePts[routePts.length - 1];
  const prev = routePts[routePts.length - 2];
  const arrowAngle =
    last && prev
      ? (Math.atan2(last[1] - ((prev[1] + last[1]) / 2 - Math.hypot(last[0] - prev[0], last[1] - prev[1]) * 0.18), last[0] - (prev[0] + last[0]) / 2) * 180) / Math.PI
      : 0;
  const stroke = 1.4 / scale;

  return (
    <Stage>
      <FitBox area={area}>
        <div style={{ position: "relative", width: totalW, height: totalH }}>
          <div
            style={{
              position: "absolute",
              left: offsetX,
              top: TOP_ROOM,
              width: mapW,
              height: mapH,
              opacity: sheet.opacity,
              transform: `translateY(${sheet.y}px) rotate(${-0.8 + sheet.rotate}deg) scale(${sheet.scale})`,
            }}
          >
            <div style={{ position: "absolute", inset: 0, transform: "translate(4px, 6px)", background: shade, clipPath: edge }} />
            <div style={{ position: "absolute", inset: 0, background: colors.cream, clipPath: edge, overflow: "hidden" }}>
              <svg width={mapW} height={mapH} viewBox={`${vx} ${vy} ${vw} ${vh}`} style={{ display: "block" }}>
                <g transform={`translate(${1.6 / scale} ${2.4 / scale})`} fill="rgba(31,26,20,.16)">
                  {Object.entries(COUNTRIES).map(([code, c]) => (
                    <path key={code} d={c.d} />
                  ))}
                </g>
                <g fill={LAND} stroke={LAND_EDGE} strokeWidth={stroke} strokeLinejoin="round">
                  {Object.entries(COUNTRIES).map(([code, c]) => (
                    <path key={code} d={c.d} />
                  ))}
                </g>
                {pins.map((p) => {
                  const on = tween(frame, p.at, 10);
                  return <path key={`hl-${p.code}`} d={COUNTRIES[p.code].d} fill={colors[accent]} opacity={on} stroke={LAND_EDGE} strokeWidth={stroke} />;
                })}
              </svg>
            </div>
          </div>
          {pins.map((p) =>
            p.small ? (
              <div
                key={`dot-${p.code}`}
                style={{
                  position: "absolute",
                  left: p.x - 20,
                  top: p.y - 20,
                  width: 40,
                  height: 40,
                  borderRadius: "50%",
                  border: `7px solid ${colors[accent]}`,
                  opacity: tween(frame, p.at, 8),
                  transform: `scale(${0.9 + 0.1 * tween(frame, p.at, 8)})`,
                }}
              />
            ) : null,
          )}
          {route.length >= 2 ? (
            <svg width={totalW} height={totalH} style={{ position: "absolute", left: 0, top: 0, overflow: "visible" }}>
              <path d={routeD} fill="none" stroke={shade} strokeWidth={9} strokeLinecap="round" transform="translate(3 4)" strokeDasharray={`${routeLen * routeDraw} ${routeLen * 2}`} />
              <path d={routeD} fill="none" stroke={colors.ink} strokeWidth={9} strokeLinecap="round" strokeDasharray={`${routeLen * routeDraw} ${routeLen * 2}`} />
              {routeDraw > 0.97 && last ? (
                <polygon
                  points="0,-16 30,0 0,16"
                  fill={colors.ink}
                  transform={`translate(${last[0] + offsetX} ${last[1]}) rotate(${arrowAngle}) translate(-22 0)`}
                />
              ) : null}
            </svg>
          ) : null}
          {pins.map((p, i) => {
            const e = entry(frame, p.at, { dy: -40, spin: 0, from: 0.9 });
            const bounce = beat && beat.index % pins.length === i ? beat.wave : 0;
            return (
              <React.Fragment key={`pin-${p.code}`}>
                <div
                  style={{
                    position: "absolute",
                    left: p.x - PIN / 2,
                    top: p.y - PIN * 1.6,
                    width: PIN,
                    height: PIN * 1.6,
                    opacity: e.opacity,
                    transform: `translateY(${e.y - 22 * bounce}px) scale(${1 + 0.2 * bounce})`,
                    transformOrigin: "50% 100%",
                  }}
                >
                  <div style={{ position: "absolute", left: PIN / 2 - 3, top: PIN * 0.6, width: 6, height: PIN, background: colors.ink }} />
                  <div style={{ position: "absolute", left: 2, top: 2, width: PIN, height: PIN, borderRadius: "50%", background: shade }} />
                  <div style={{ position: "absolute", left: 0, top: 0, width: PIN, height: PIN, borderRadius: "50%", background: colors.ink }} />
                  <div style={{ position: "absolute", left: PIN * 0.28, top: PIN * 0.22, width: PIN * 0.3, height: PIN * 0.3, borderRadius: "50%", background: colors.cream }} />
                </div>
                {p.label ? (
                  <div style={{ position: "absolute", left: p.left, top: p.ly }}>
                    <PaperStrip text={p.label} fontSize={labelSize} enterAt={p.at + 3} seed={`map-label-${p.code}`} float={2} motion={{ dy: -20, dx: 0 }} />
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
        </div>
      </FitBox>
    </Stage>
  );
};

