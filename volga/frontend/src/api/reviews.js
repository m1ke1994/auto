import { getJsonSectionItems, toPublicMediaUrl } from "./publicSite"

export const getReviews = async () => {
  const items = await getJsonSectionItems("reviews")
  return items.map((item, index) => ({
    id: item?.id ?? `review-${index}`,
    name: String(item?.name || ""),
    event_name: String(item?.event_name || ""),
    rating: Number(item?.rating || 0),
    text: String(item?.text || ""),
    date: item?.date || null,
    avatar: toPublicMediaUrl(item?.avatar),
  }))
}
