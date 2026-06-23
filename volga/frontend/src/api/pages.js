import { getJsonSectionItems } from "./publicSite"

export async function getPage(slug) {
  const pages = await getJsonSectionItems("pages")
  const data = pages.find((page) => String(page?.slug || "") === String(slug || "")) || {}
  if (!data.slug) {
    throw new Error(`page not found: ${slug}`)
  }

  const sections = Array.isArray(data.sections)
    ? data.sections.map((section, index) => ({
        ...section,
        order: Number.isFinite(Number(section?.order)) ? Number(section.order) : index,
      }))
    : []

  const gallery = Array.isArray(data.gallery)
    ? data.gallery
        .map((item, index) => ({
          id: item?.id ?? `gallery-${index}`,
          image: String(item?.image || "").trim(),
          order: Number.isFinite(Number(item?.order)) ? Number(item.order) : index,
        }))
        .filter((item) => item.image)
        .sort((a, b) => a.order - b.order)
    : []

  return {
    ...data,
    sections,
    gallery,
  }
}
