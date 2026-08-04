import { describe, expect, it } from "vitest";
import { mergePortfolioContent, normalizeImageList, normalizeStringList } from "@/lib/tracknode";

describe("TrackNode portfolio content helpers", () => {
  it("merges remote section content over local defaults without dropping other sections", () => {
    const merged = mergePortfolioContent(
      {
        hero: { title: "Local title", subtitle: "Local subtitle" },
        contact: { title: "Contact" },
      },
      [{ key: "hero", title: "Hero", content: { title: "Admin title" } }],
    );

    expect(merged.hero).toEqual({ title: "Admin title", subtitle: "Local subtitle" });
    expect(merged.contact).toEqual({ title: "Contact" });
  });

  it("normalizes TrackNode repeater rows and legacy arrays", () => {
    expect(normalizeStringList(["React", { label: "Django" }, { label: "" }])).toEqual(["React", "Django"]);
    expect(normalizeImageList(["/one.jpg", { src: "/two.jpg" }, { url: "/three.jpg" }])).toEqual([
      "/one.jpg",
      "/two.jpg",
      "/three.jpg",
    ]);
  });
});
