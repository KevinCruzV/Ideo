import { cancelRender, continueRender, delayRender } from "remotion";
import bricolageUrl from "../public/fonts/BricolageGrotesque-Variable.ttf";
import unboundedUrl from "../public/fonts/Unbounded-Variable.ttf";

const faces = [
  { family: "Bricolage Grotesque", url: bricolageUrl, weight: "200 800" },
  { family: "Unbounded", url: unboundedUrl, weight: "200 900" },
];

let loading: Promise<void> | null = null;

export const loadFonts = (): Promise<void> => {
  if (loading) return loading;
  const handle = delayRender("fonts");
  loading = Promise.all(
    faces.map(async ({ family, url, weight }) => {
      const face = new FontFace(family, `url(${url})`, { weight, style: "normal" });
      await face.load();
      (document.fonts as unknown as { add(face: FontFace): void }).add(face);
    }),
  )
    .then(() => document.fonts.ready)
    .then(() => continueRender(handle))
    .catch((err: unknown) => cancelRender(err));
  return loading;
};
