import { beforeEach, describe, expect, it } from "vitest";
import fs from "node:fs";
import { projects } from "@/data/projects";
import {
  applySeo,
  mergePortfolioContent,
  normalizeImageList,
  normalizePortfolioProject,
  normalizePortfolioServices,
  normalizeProjectImages,
  normalizeStringList,
  resolveMediaUrl,
} from "@/lib/tracknode";

beforeEach(() => {
  document.head.innerHTML = "";
  document.title = "Portfolio";
});

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

  it("normalizes TrackNode repeater rows", () => {
    expect(normalizeStringList(["React", { label: "Django" }, { label: "" }])).toEqual(["React", "Django"]);
  });

  it("normalizes editable portfolio services for section and form usage", () => {
    expect(
      normalizePortfolioServices([
        { id: "b", title: "Second", category: "Dev", order: 20 },
        { id: "a", title: "First", category: "Dev", order: 10 },
        { id: "hidden", title: "Hidden", is_active: false },
        { title: "" },
      ]).map((service) => service.title),
    ).toEqual(["First", "Second"]);
  });

  it("keeps absolute media URLs unchanged", () => {
    expect(resolveMediaUrl("https://cdn.example.com/photo.webp", "https://tracknode.ru")).toBe(
      "https://cdn.example.com/photo.webp",
    );
  });

  it("resolves backend media URLs against the backend domain", () => {
    expect(resolveMediaUrl("/media/sites/161/projects/photo.webp", "https://tracknode.ru")).toBe(
      "https://tracknode.ru/media/sites/161/projects/photo.webp",
    );
  });

  it("keeps bundled public asset paths relative to the portfolio domain", () => {
    expect(resolveMediaUrl("/beauty-salon-website-psi.vercel.JPG", "https://tracknode.ru")).toBe(
      "/beauty-salon-website-psi.vercel.JPG",
    );
  });

  it("keeps data and blob URLs unchanged", () => {
    expect(resolveMediaUrl("data:image/png;base64,abc", "https://tracknode.ru")).toBe("data:image/png;base64,abc");
    expect(resolveMediaUrl("blob:https://site.example/123", "https://tracknode.ru")).toBe("blob:https://site.example/123");
  });

  it("normalizes image repeater rows and legacy arrays", () => {
    expect(
      normalizeImageList([
        "/one.jpg",
        { image: "/media/sites/161/projects/main.webp" },
        { src: "/two.jpg" },
        { url: "/three.jpg" },
      ]),
    ).toEqual([
      "/one.jpg",
      `${window.location.origin}/media/sites/161/projects/main.webp`,
      "/two.jpg",
      "/three.jpg",
    ]);
  });

  it("prefers projects[].image over legacy images[]", () => {
    expect(
      normalizeProjectImages({
        image: "/media/sites/161/projects/main.webp",
        images: [{ src: "/legacy.jpg" }],
      }),
    ).toEqual([`${window.location.origin}/media/sites/161/projects/main.webp`, "/legacy.jpg"]);
  });

  it("deduplicates project images after resolving URLs", () => {
    expect(
      normalizeProjectImages({
        image: "/media/sites/161/projects/main.webp",
        images: [{ src: "/media/sites/161/projects/main.webp" }],
      }),
    ).toEqual([`${window.location.origin}/media/sites/161/projects/main.webp`]);
  });

  it("normalizes a complete portfolio project from admin content", () => {
    const project = normalizePortfolioProject({
      title: "TrackNode",
      image: "/media/sites/161/projects/tracknode.webp",
      image_alt: "Dashboard screenshot",
      images: [],
      techStack: [{ label: "Vue" }, "Django"],
    });

    expect(project.images).toEqual([`${window.location.origin}/media/sites/161/projects/tracknode.webp`]);
    expect(project.techStack).toEqual(["Vue", "Django"]);
    expect(project.image_alt).toBe("Dashboard screenshot");
  });

  it("falls back to legacy project images when projects[].image is empty", () => {
    const project = normalizePortfolioProject({
      title: "Legacy",
      images: [{ src: "/legacy.jpg" }],
      techStack: [],
    });

    expect(project.images).toEqual(["/legacy.jpg"]);
    expect(project.image_alt).toBe("Legacy");
  });

  it("applies media OG image as an absolute backend URL", () => {
    applySeo({
      id: 1,
      name: "Portfolio",
      slug: "my-portfolio",
      domain: "tishechkinalexandr.ru",
      seo: { title: "Admin title", og_image: "/media/sites/161/seo/og.webp" },
    });

    expect(document.querySelector<HTMLMetaElement>('meta[property="og:image"]')?.content).toBe(
      `${window.location.origin}/media/sites/161/seo/og.webp`,
    );
  });

  it("applies favicon from runtime settings", () => {
    applySeo(undefined, { favicon: "/media/sites/161/settings/favicon.webp" });

    expect(document.querySelector<HTMLLinkElement>('link[rel="icon"]')?.href).toBe(
      `${window.location.origin}/media/sites/161/settings/favicon.webp`,
    );
  });

  it("keeps canonical URL from SEO payload", () => {
    applySeo({
      id: 1,
      name: "Portfolio",
      slug: "my-portfolio",
      domain: "tishechkinalexandr.ru",
      seo: { canonical: "https://tishechkinalexandr.ru/" },
    });

    expect(document.querySelector<HTMLLinkElement>('link[rel="canonical"]')?.href).toBe(
      "https://tishechkinalexandr.ru/",
    );
  });

  it("updates existing SEO tags instead of duplicating them", () => {
    applySeo(undefined, { site_title: "First title", description: "First description" });
    applySeo(undefined, { site_title: "Second title", description: "Second description" });

    expect(document.querySelectorAll('meta[name="description"]')).toHaveLength(1);
    expect(document.querySelector<HTMLMetaElement>('meta[name="description"]')?.content).toBe("Second description");
    expect(document.title).toBe("Second title");
  });

  it("keeps portfolio SEO separate from TrackNode SEO", () => {
    const html = fs.readFileSync("index.html", "utf8");

    expect(html).toContain('href="https://tishechkinalexandr.ru/"');
    expect(html).toContain('og:site_name" content="Портфолио Александра Тишечкина"');
    expect(html).toContain('href="/favicon.svg"');
    expect(html).not.toContain('rel="canonical" href="https://tracknode.ru/"');
  });

  it("has a TrackNode project card with a direct public link", () => {
    const trackNodeProject = projects.find((project) => project.demoUrl === "https://tracknode.ru/");

    expect(trackNodeProject?.title).toContain("TrackNode");
    expect(trackNodeProject?.shortDescription).toContain("аналитику");
    expect(trackNodeProject?.shortDescription).toContain("создание");
  });
});
