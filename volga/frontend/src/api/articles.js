import { getJsonSectionItems, toPublicMediaUrl } from "./publicSite"

const normalizeItem = (item) => ({
  title: String(item?.title || ""),
  slug: String(item?.slug || ""),
  preview_image: toPublicMediaUrl(item?.preview_image),
  preview_description: String(item?.preview_description || ""),
  content: String(item?.content || ""),
  content_type: String(item?.content_type || "article"),
  video_url: String(item?.video_url || ""),
  created_at: item?.created_at || item?.published_date || null,
})

export const getArticles = async () => {
  const items = await getJsonSectionItems("articles")
  return items.map(normalizeItem)
}

export const getArticleBySlug = async (slug) => {
  const safeSlug = encodeURIComponent(String(slug || "").trim())
  if (!safeSlug) throw new Error("article slug is required")

  const items = await getArticles()
  const item = items.find((article) => article.slug === safeSlug)
  if (!item) throw new Error(`article not found: ${safeSlug}`)
  return item
}
