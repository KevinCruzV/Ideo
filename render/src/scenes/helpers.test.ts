import { describe, expect, test } from "vitest";
import { cleanItems, initials, str, strList, unitList } from "./coerce";
import { fitText, splitKey, textWidth } from "./fit";
import { enterFor, stateIndex, stateTimes } from "./timing";

describe("coerce", () => {
  test("les props mal typées donnent des valeurs sûres", () => {
    expect(str(null)).toBe("");
    expect(str(42)).toBe("42");
    expect(str({ text: "objet" })).toBe("objet");
    expect(str("a \u2014 b")).toBe("a , b");
    expect(strList("un;deux", 6)).toEqual(["un", "deux"]);
    expect(strList([1, null, "trois"], 6)).toEqual(["1", "trois"]);
    expect(unitList([1, "0.5", null, 2], 8)).toEqual([0.5, 0.25, 0, 1]);
    expect(cleanItems([{ el: "a", at: 3 }, { el: "b" }, "x", null])).toEqual([{ el: "a", at: 3 }]);
  });

  test("initiales", () => {
    expect(initials("Hermann Ebbinghaus")).toBe("HE");
    expect(initials("Marie Curie-Skłodowska")).toBe("MS");
    expect(initials("")).toBe("?");
  });
});

describe("fit", () => {
  test("le texte tient dans la largeur et le nombre de lignes", () => {
    const long = "un texte très long qui ne tiendra jamais sur une seule ligne de neuf cents pixels à cette taille";
    const fit = fitText(long, { maxWidth: 900, maxLines: 2, max: 96, min: 44 });
    expect(fit.lines.length).toBeLessThanOrEqual(2);
    expect(fit.size).toBeGreaterThanOrEqual(44);
    fit.lines.forEach((l) => expect(textWidth(l, fit.size) + fit.size * 0.6).toBeLessThanOrEqual(900));
  });

  test("le mot clé est trouvé ou le plus long est choisi", () => {
    expect(splitKey("La courbe de l'oubli", "l'oubli")).toEqual({ before: "La courbe de", key: "l'oubli", after: "" });
    expect(splitKey("Dis-moi pourquoi tu oublies").key).toBe("pourquoi");
    expect(splitKey("").key).toBe("");
  });
});

describe("timing", () => {
  const items = [
    { el: "values.1", at: 120 },
    { el: "values.2", at: 5000 },
  ];
  test("les images absolues deviennent locales et restent dans le segment", () => {
    expect(enterFor("values.0", items, 100, 190)).toBe(0);
    expect(enterFor("values.1", items, 100, 190)).toBe(20);
    expect(enterFor("values.2", items, 100, 190)).toBe(82);
  });

  test("l'état courant suit les éléments ou se répartit seul", () => {
    const listed = stateTimes("states", 3, [{ el: "states.1", at: 130 }, { el: "states.2", at: 160 }], 100, 190);
    expect(listed).toEqual([0, 30, 60]);
    expect(stateIndex(listed, 45)).toBe(1);
    expect(stateTimes("states", 3, [], 0, 90)).toEqual([0, 30, 60]);
  });
});
