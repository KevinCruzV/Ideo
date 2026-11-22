import React from "react";
import { continueRender, delayRender } from "remotion";
import { loadFonts } from "../fonts";
import { STAGE_H } from "./Stage";

export type Area = { left: number; top: number; width: number; height: number };

export const AREA_BOTTOM_GAP = 26;

export const fitScale = (content: { width: number; height: number }, area: { width: number; height: number }, maxScale = 1): number => {
  if (content.width <= 0 || content.height <= 0) return 1;
  return Math.min(maxScale, area.width / content.width, area.height / content.height);
};

export const areaFor = (top: number, left: number, width: number, bottomGap = AREA_BOTTOM_GAP): Area => ({
  left,
  top,
  width,
  height: Math.max(100, STAGE_H - top - bottomGap),
});

export const FitBox: React.FC<{ area: Area; maxScale?: number; valign?: "center" | "top"; children: React.ReactNode }> = ({
  area,
  maxScale = 1,
  valign = "center",
  children,
}) => {
  const ref = React.useRef<HTMLDivElement>(null);
  const [size, setSize] = React.useState<{ width: number; height: number } | null>(null);
  const [handle] = React.useState(() => delayRender("fit-box"));

  React.useLayoutEffect(() => {
    let alive = true;
    loadFonts()
      .then(() => {
        if (!alive || !ref.current) return;
        setSize({ width: ref.current.offsetWidth, height: ref.current.offsetHeight });
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
    return () => {
      alive = false;
    };
  }, [handle]);

  const scale = size ? fitScale(size, area, maxScale) : 1;
  const w = (size?.width ?? 0) * scale;
  const h = (size?.height ?? 0) * scale;
  const left = area.left + (area.width - w) / 2;
  const top = valign === "top" ? area.top : area.top + (area.height - h) / 2;

  return (
    <div
      ref={ref}
      data-fit-scale={scale.toFixed(3)}
      style={{
        position: "absolute",
        left,
        top,
        width: "max-content",
        transform: `scale(${scale})`,
        transformOrigin: "0 0",
        visibility: size ? "visible" : "hidden",
      }}
    >
      {children}
    </div>
  );
};

export const largestFitting = (from: number, to: number, fits: (value: number) => boolean, step = 2): number => {
  for (let v = from; v > to; v -= step) if (fits(v)) return v;
  return to;
};
