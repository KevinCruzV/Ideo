import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { colors, fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { initials, str } from "./coerce";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { Stage, STAGE_W } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

const AVATAR = 420;

export const PersonCard: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const name = str(props.name, "?");
  const role = str(props.role);
  const nameFit = fitText(name, { maxWidth: 900, maxLines: 2, max: 104, min: 56 });
  const roleFit = fitText(role, { maxWidth: 860, maxLines: 3, max: 58, min: 44 });
  const letters = initials(name);
  const left = (STAGE_W - AVATAR) / 2;

  return (
    <Stage>
      <PaperShape kind="square" color="cream" size={360} x={left - 90} y={110} rotate={-9} seed="pc-back" />
      <PaperShape
        kind="circle"
        color={accent}
        size={AVATAR}
        x={left + 20}
        y={50}
        enterAt={enterFor("avatar", items, from, to)}
        seed="pc-avatar"
        wobble={0.5}
      >
        <span
          style={{
            fontFamily: fonts.text,
            fontWeight: 800,
            fontSize: letters.length > 1 ? 180 : 220,
            color: onPaper[accent],
            letterSpacing: -4,
            lineHeight: 1,
          }}
        >
          {letters}
        </span>
      </PaperShape>
      <div
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          top: 540,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 22,
          color: colors.ink,
        }}
      >
        <Strips lines={nameFit.lines} size={nameFit.size} enterAt={enterFor("name", items, from, to)} seed="pc-name" />
        <Strips
          lines={roleFit.lines}
          size={roleFit.size}
          color="ink"
          enterAt={enterFor("role", items, from, to)}
          seed="pc-role-x"
          gap={10}
        />
      </div>
    </Stage>
  );
};
