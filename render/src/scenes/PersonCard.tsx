import React from "react";
import { useCurrentFrame } from "remotion";
import { drift, entry, paperTransform } from "../paper/motion";
import { colors, onPaper } from "../theme";
import { useAccent } from "./accent";
import { Backdrop } from "./Backdrop";
import { initials, str } from "./coerce";
import { fitText } from "../text/fit";
import { bustHeight, BUST_VIEW, PersonBust } from "./PersonBust";
import { lookOf } from "./personLook";
import { hasVisual, Picto } from "../pictos/Picto";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { areaFor, FitBox } from "./FitBox";
import { enterFor } from "./timing";

const BUST_W = 600;
const BUST_H = bustHeight(BUST_W);
const HEAD_Y = ((40 - BUST_VIEW.y) / BUST_VIEW.h) * BUST_H;

export const PersonCard: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const accent = useAccent();
  const name = str(props.name, "?");
  const role = str(props.role);
  const nameFit = fitText(name, { maxWidth: hasVisual(props.picto) ? BOX_W - 180 : BOX_W, maxLines: 2, max: 110, min: 60, prefer: true });
  const roleFit = fitText(role, { maxWidth: BOX_W - 40, maxLines: 4, max: 62, min: 44, prefer: true });
  const letters = initials(name);
  const top = areaTop(props);
  const bust = entry(frame, -3, { dy: 70, spin: 0, from: 0.94 });
  const sway = drift("pc-bust", frame, 2, 0.3);
  const nameAt = enterFor("name", items, from, to);
  const badge = accent === "yellow" ? colors.red : colors.yellow;
  const look = React.useMemo(() => lookOf(props), [props]);
  const flag = hasVisual(props.picto);

  return (
    <Stage>
      <FitBox area={areaFor(top + 10, BOX_L, BOX_W)} maxScale={1.1}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40, width: BOX_W }}>
          <div style={{ position: "relative", width: BUST_W, height: BUST_H }}>
            <Backdrop color={accent} size={580} cx={BUST_W / 2} cy={HEAD_Y + 50} seed="pc-disk" turn={6} />
            <div
              style={{
                position: "absolute",
                inset: 0,
                opacity: bust.opacity,
                transform: paperTransform(bust, sway, 0),
                transformOrigin: "50% 100%",
              }}
            >
              <PersonBust width={BUST_W} initials={letters} badge={badge} badgeInk={onPaper[accent === "yellow" ? "red" : "yellow"]} look={look} accent={accent} />
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 26 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
              {flag ? <Picto name={props.picto} size={Math.round(nameFit.size * 1.5)} rotate={-5} react={false} /> : null}
              <Strips lines={nameFit.lines} size={nameFit.size} enterAt={nameAt} seed="pc-name" />
            </div>
            <Strips lines={roleFit.lines} size={roleFit.size} color="ink" enterAt={Math.max(nameAt + 6, enterFor("role", items, from, to))} seed="pc-role" gap={10} />
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
