import React from "react";
import { PaperShape } from "../paper/PaperShape";
import { Picto } from "../pictos/Picto";
import { fonts, onPaper } from "../theme";
import { useAccent } from "./accent";
import { str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import { fitText } from "../text/fit";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";
import { useBeat } from "./beats";
import { AudioWave, useSegmentAudio } from "../chrome/AudioWave";

const MARK = 160;

export const Quote: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const accent = useAccent();
  const beat = useBeat();
  const kick = beat && beat.index % 2 === 0 ? beat.wave : 0;
  const text = fitText(str(props.text, "…"), { maxWidth: BOX_W, maxLines: 8, max: 80, min: 56 });
  const speaker = fitText(str(props.speaker), { maxWidth: BOX_W - 100, maxLines: 1, max: 54, min: 44 });
  const textAt = enterFor("text", items, from, to);
  const audio = useSegmentAudio();

  return (
    <Stage>
      <FitBox area={areaFor(areaTop(props) + 10, BOX_L, BOX_W)} maxScale={1.1}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 36, width: BOX_W }}>
          <div style={{ position: "relative", width: BOX_W, height: MARK }}>
            <PaperShape kind="square" color={accent} size={MARK} x={6} y={0} rotate={-8 - 12 * kick} seed="quote-mark" float={3} style={{ scale: String(1 + 0.18 * kick) }}>
              <span style={{ fontFamily: fonts.text, fontWeight: 800, fontSize: 180, lineHeight: 1, marginTop: 26, color: onPaper[accent] }}>«</span>
            </PaperShape>
            {audio ? null : <Picto name={props.picto} size={190} x={BOX_W - 200} y={-20} rotate={6} />}
            {audio ? (
              <div style={{ position: "absolute", left: MARK + 40, top: 10 }}>
                <AudioWave levels={audio.levels} start={audio.start} accent={accent} width={BOX_W - MARK - 60} height={MARK - 20} />
              </div>
            ) : null}
          </div>
          <Strips lines={text.lines} size={text.size} enterAt={textAt} stagger={3} align="flex-start" seed="quote-text" gap={10} motion={{ dx: -40, dy: 0 }} />
          {speaker.lines.length > 0 ? (
            <Strips
              lines={speaker.lines}
              size={speaker.size}
              color="ink"
              enterAt={items.some((i) => i.el === "speaker") ? enterFor("speaker", items, from, to) : textAt + 10}
              align="flex-end"
              seed="quote-speaker"
              style={{ alignSelf: "flex-end" }}
            />
          ) : null}
        </div>
      </FitBox>
    </Stage>
  );
};
