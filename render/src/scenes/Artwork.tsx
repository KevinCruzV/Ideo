import React from "react";
import { useCurrentFrame } from "remotion";
import { drift, entry, paperTransform } from "../paper/motion";
import { fitText } from "../text/fit";
import { photoSource, str } from "./coerce";
import { areaFor, FitBox } from "./FitBox";
import { ART_H, ART_W, PhotoFrame } from "./PhotoFrame";
import type { SceneProps } from "./registry";
import { areaTop, BOX_L, BOX_W, Stage } from "./Stage";
import { Strips } from "./Strips";
import { enterFor } from "./timing";

export const Artwork: React.FC<SceneProps> = ({ props, items, from, to }) => {
  const frame = useCurrentFrame();
  const title = fitText(str(props.title, "?"), { maxWidth: BOX_W, maxLines: 2, max: 96, min: 56, prefer: true });
  const artist = fitText(str(props.artist), { maxWidth: BOX_W - 40, maxLines: 2, max: 60, min: 44, prefer: true });
  const image = photoSource(props.image);
  const titleAt = enterFor("title", items, from, to);
  const artistAt = Math.max(titleAt + 6, enterFor("artist", items, from, to));
  const picture = entry(frame, -3, { dy: 70, spin: 0, from: 0.94 });
  const sway = drift("art-frame", frame, 2, 0.3);

  return (
    <Stage>
      <FitBox area={areaFor(areaTop(props) + 10, BOX_L, BOX_W)} maxScale={1.1}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 44, width: BOX_W }}>
          {image ? (
            <div style={{ opacity: picture.opacity, transform: paperTransform(picture, sway, -1.5), transformOrigin: "50% 100%" }}>
              <PhotoFrame src={image} seed="art-frame" width={ART_W} height={ART_H} whole />
            </div>
          ) : null}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
            <Strips lines={title.lines} size={title.size} enterAt={titleAt} seed="art-title" />
            <Strips lines={artist.lines} size={artist.size} color="ink" enterAt={artistAt} seed="art-artist" gap={10} />
          </div>
        </div>
      </FitBox>
    </Stage>
  );
};
