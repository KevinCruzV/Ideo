import React from "react";
import { Segment } from "../types";
import { Placeholder } from "./Placeholder";

export type SceneProps = { segment: Segment };

export const scenes: Record<string, React.ComponentType<SceneProps>> = {};

export const resolveScene = (segment: Segment): React.ComponentType<SceneProps> => {
  const key = segment.kind === "scene" && segment.type ? segment.type : segment.kind;
  return scenes[key] ?? Placeholder;
};
