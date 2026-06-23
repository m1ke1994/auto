import { getJsonSectionItems, toPublicMediaUrl } from "./publicSite"

const normalizeNewsContent = (value) => {
  if (Array.isArray(value)) {
    return value.map((paragraph) => String(paragraph || "")).filter(Boolean)
  }

  if (value == null) return ""
  return String(value)
}

const normalizeNews = (item) => ({
  id: item?.id ?? null,
  title: String(item?.title || ""),
  slug: String(item?.slug || ""),
  description: String(item?.description || ""),
  image: toPublicMediaUrl(item?.image),
  published_date: item?.published_date || null,
  content: normalizeNewsContent(item?.content),
})

export const getNewsList = async () => {
  const items = await getJsonSectionItems("news")
  return items.map(normalizeNews)
}

export const getNewsBySlug = async (slug) => {
  const safeSlug = encodeURIComponent(String(slug || "").trim())
  if (!safeSlug) throw new Error("news slug is required")

  const items = await getNewsList()
  const item = items.find((newsItem) => newsItem.slug === safeSlug)
  if (!item) throw new Error(`news not found: ${safeSlug}`)
  return item
}
