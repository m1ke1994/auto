import { MAIN_MENU_ITEMS } from "../data/navigation"
import { getJsonSectionItems } from "./publicSite"

function normalizeNavigationItem(item) {
  const label = String(item?.label || "").trim()
  const to = String(item?.to || "").trim()
  const href = String(item?.href || "").trim()

  if (!label || (!to && !href)) return null
  return href ? { label, href } : { label, to }
}

export async function getNavigationItems() {
  try {
    const items = await getJsonSectionItems("navigation")
    const normalized = items.map(normalizeNavigationItem).filter(Boolean)
    return normalized.length ? normalized : MAIN_MENU_ITEMS
  } catch (error) {
    console.error("[navigation] failed to load", error)
    return MAIN_MENU_ITEMS
  }
}
