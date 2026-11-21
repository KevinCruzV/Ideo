import React from "react";
import { CalculateMetadataFunction, Composition } from "remotion";
import minimal from "../fixtures/minimal.json";
import { loadFonts } from "./fonts";
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
);
