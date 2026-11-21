import React from "react";
import { useCurrentFrame } from "remotion";
import { drift, entry, paperTransform } from "../paper/motion";
import { colors, onPaper } from "../theme";
import { useAccent } from "./accent";
import { Backdrop } from "./Backdrop";
import { initials, str } from "./coerce";
import { fitText } from "../text/fit";
import { PersonBust } from "./PersonBust";
import type { SceneProps } from "./registry";
import { areaTop, BOX_CX, BOX_W, Stage, STAGE_H } from "./Stage";
import { Strips, stripsHeight } from "./Strips";
import { enterFor } from "./timing";

const BUST_W = 600;
const BUST_H = (BUST_W * 128) / 200;

export const PersonCard: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const name = str(props.name, "?");
  const role = str(props.role);
  const nameFit = fitText(name, { maxWidth: BOX_W, maxLines: 2, max: 110, min: 60, prefer: true });
  const roleFit = fitText(role, { maxWidth: BOX_W - 40, maxLines: 3, max: 62, min: 40, prefer: true });
  const letters = initials(name);
  const top = areaTop(props);
  const textH = stripsHeight(nameFit.lines.length, nameFit.size) + 26 + stripsHeight(roleFit.lines.length, roleFit.size, 10);
  const total = BUST_H + 40 + textH;
  const y0 = top + Math.max(0, (STAGE_H - top - total) / 2);
  const bust = entry(frame, -3, { dy: 70, spin: 0, from: 0.94 });
  const sway = drift("pc-bust", frame, 2, 0.3);
  const nameAt = enterFor("name", items, from, to);
  const badge = accent === "yellow" ? colors.red : colors.yellow;

  return (
    <Stage>
      <Backdrop color={accent} size={560} cx={BOX_CX} cy={y0 + BUST_H * 0.48} seed="pc-disk" turn={6} />
      <div
        style={{
          position: "absolute",
          left: BOX_CX - BUST_W / 2,
          top: y0,
          width: BUST_W,
          height: BUST_H,
          opacity: bust.opacity,
          transform: paperTransform(bust, sway, 0),
          transformOrigin: "50% 100%",
        }}
      >
        <PersonBust width={BUST_W} initials={letters} badge={badge} badgeInk={onPaper[accent === "yellow" ? "red" : "yellow"]} />
      </div>
      <div
        style={{
          position: "absolute",
          left: BOX_CX - BOX_W / 2,
          width: BOX_W,
          top: y0 + BUST_H + 40,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 26,
        }}
      >
        <Strips lines={nameFit.lines} size={nameFit.size} enterAt={nameAt} seed="pc-name" />
        <Strips lines={roleFit.lines} size={roleFit.size} color="ink" enterAt={Math.max(nameAt + 6, enterFor("role", items, from, to))} seed="pc-role" gap={10} />
      </div>
    </Stage>
  );
};
