import React from "react";
import { Segment, TimelineItem } from "../types";
import { Counter } from "./Counter";
import { FactChips } from "./FactChips";
import { Hook } from "./Hook";
import { IconGrid } from "./IconGrid";
import { KeyTitle } from "./KeyTitle";
import { Mascot } from "./Mascot";
import { ObjectState } from "./ObjectState";
import { Outro } from "./Outro";
import { PersonCard } from "./PersonCard";
import { Placeholder } from "./Placeholder";
import { Quote } from "./Quote";
import { ShapeDiagram } from "./ShapeDiagram";
import { StackList } from "./StackList";
import { Stamp } from "./Stamp";
import { Timeline } from "./Timeline";
import { Versus } from "./Versus";
import { MapScene } from "./MapScene";
import { BodyScene } from "./BodyScene";

export type SceneType =
  | "hook"
  | "outro"
  | "key-title"
  | "person-card"
  | "fact-chips"
  | "stack-list"
  | "counter"
  | "timeline"
  | "icon-grid"
  | "stamp"
  | "quote"
  | "object-state"
  | "shape-diagram"
  | "mascot"
  | "versus"
  | "map"
  | "body";

export type SceneProps = {
  props: Record<string, unknown>;
  items: TimelineItem[];
  from: number;
  to: number;
};

export const SCENES: Record<SceneType, React.FC<SceneProps>> = {
  hook: Hook,
  outro: Outro,
  "key-title": KeyTitle,
  "person-card": PersonCard,
  "fact-chips": FactChips,
  "stack-list": StackList,
  counter: Counter,
  timeline: Timeline,
  "icon-grid": IconGrid,
  stamp: Stamp,
  quote: Quote,
  "object-state": ObjectState,
  "shape-diagram": ShapeDiagram,
  mascot: Mascot,
  versus: Versus,
  map: MapScene,
  body: BodyScene,
};

export const sceneKey = (segment: Segment): string =>
  segment.kind === "scene" && segment.type ? segment.type : segment.kind;

export const resolveScene = (segment: Segment): React.FC<SceneProps> =>
  (SCENES as Record<string, React.FC<SceneProps>>)[sceneKey(segment)] ?? Placeholder;
