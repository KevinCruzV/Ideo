import { expect, test } from "vitest";
import { SCENES, SceneType } from "./registry";

test("chaque type de plan_check a un composant", () => {
  const types = ["key-title","person-card","fact-chips","stack-list","counter","timeline",
                 "icon-grid","stamp","quote","object-state","shape-diagram","mascot"];
  types.forEach((t) => expect(SCENES[t as SceneType]).toBeDefined());
});
