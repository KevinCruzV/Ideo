import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import minimal from "../fixtures/minimal.json";
import { loadFonts } from "./fonts";
import { Cover, COVER_FRAMES, CoverProps } from "./Cover";
import { FLAG_SHEET_H, FLAG_SHEET_W, FlagSheet } from "./pictos/FlagSheet";
import { PictoSheet, SHEET_H, SHEET_W } from "./pictos/PictoSheet";
import { PERSON_SHEET_H, PERSON_SHEET_W, PersonSheet } from "./scenes/PersonSheet";
import { Short } from "./Short";
import { Timeline } from "./types";

loadFonts();

const calculateMetadata: CalculateMetadataFunction<Timeline> = ({ props }) => ({
  durationInFrames: props.durationInFrames,
  fps: props.fps,
  width: props.width,
  height: props.height,
});

export const Root: React.FC = () => (
  <>
    <Composition
      id="Short"
      component={Short}
      durationInFrames={minimal.durationInFrames}
      fps={minimal.fps}
      width={minimal.width}
      height={minimal.height}
      defaultProps={minimal as Timeline}
      calculateMetadata={calculateMetadata}
    />
    <Composition
      id="Cover"
      component={Cover}
      durationInFrames={COVER_FRAMES}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{ title: "Pourquoi le ciel est bleu", hook: "Dis-moi pourquoi le ciel est bleu et pas violet ?", picto: "sun", part: 1, total: 1, label: "Partie" } as CoverProps}
    />
    <Composition id="Pictos" component={PictoSheet} durationInFrames={1} fps={30} width={SHEET_W} height={SHEET_H} />
    <Composition id="Persons" component={PersonSheet} durationInFrames={1} fps={30} width={PERSON_SHEET_W} height={PERSON_SHEET_H} />
    <Composition id="Flags" component={FlagSheet} durationInFrames={1} fps={30} width={FLAG_SHEET_W} height={FLAG_SHEET_H} />
  </>
);
