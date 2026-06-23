import { getSectionContent } from "./publicSite"

const DEFAULT_SITE_SETTINGS = {
  phone: "+7 (985) 200-63-22",
  email: "elizaveta-struchkova@yandex.ru",
  telegram_url: "https://t.me/novoe_konakovo",
  telegram_username: "@novoe_konakovo",
  address: "Тверская область, Конаковский район, природный кластер «Новое Конаково».",
}

const normalizeTelegramUrl = (url, username) => {
  const rawUrl = String(url || "").trim()
  if (/^https?:\/\//i.test(rawUrl)) return rawUrl
  if (/^t\.me\//i.test(rawUrl)) return `https://${rawUrl}`
  if (rawUrl.startsWith("@")) return `https://t.me/${rawUrl.slice(1)}`

  const rawUsername = String(username || "").trim()
  if (rawUsername.startsWith("@")) return `https://t.me/${rawUsername.slice(1)}`
  if (rawUsername) return `https://t.me/${rawUsername}`

  return ""
}

const normalizeTelegramLabel = (username, url) => {
  const rawUsername = String(username || "").trim()
  if (rawUsername) return rawUsername.startsWith("@") ? rawUsername : `@${rawUsername}`

  const rawUrl = String(url || "").trim()
  const match = rawUrl.match(/t\.me\/([A-Za-z0-9_]+)/i)
  if (match?.[1]) {
    return `@${match[1]}`
  }

  return ""
}

const normalizeSiteSettings = (payload) => {
  const phone = String(payload?.phone || "").trim()
  const email = String(payload?.email || "").trim()
  const telegram_url = normalizeTelegramUrl(payload?.telegram_url, payload?.telegram_username)
  const telegram_username = normalizeTelegramLabel(payload?.telegram_username, telegram_url)
  const address = String(payload?.address || "").trim()

  return {
    phone,
    email,
    telegram_url,
    telegram_username,
    address,
  }
}

export async function getSiteSettings() {
  try {
    const payload = await getSectionContent("site-settings")
    return normalizeSiteSettings(payload)
  } catch (error) {
    console.error("[site-settings] failed to load", error)
    return normalizeSiteSettings(DEFAULT_SITE_SETTINGS)
  }
}
