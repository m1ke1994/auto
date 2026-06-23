import { buildApiUrl, buildBackendUrl, siteSlug } from "../config/api"

const cacheTtlMs = 5 * 60 * 1000
const cacheKey = `volga-public-site:${siteSlug}`
const trackerScriptId = "yadro-volga-tracker"
const mediaKeyPattern = /(image|video|avatar|poster|photo|src|file|url)$/i

let memoryCacheEntry = null
let pendingRequest = null

function getSessionStorage() {
  if (typeof window === "undefined") return null
  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

function isFresh(entry) {
  return Boolean(entry?.payload && Number.isFinite(entry.cachedAt) && Date.now() - entry.cachedAt < cacheTtlMs)
}

function readCache() {
  if (isFresh(memoryCacheEntry)) return memoryCacheEntry.payload

  const storage = getSessionStorage()
  if (!storage) return null

  try {
    const entry = JSON.parse(storage.getItem(cacheKey) || "null")
    if (!isFresh(entry)) return null
    memoryCacheEntry = entry
    return entry.payload
  } catch {
    return null
  }
}

function writeCache(payload) {
  const entry = { cachedAt: Date.now(), payload }
  memoryCacheEntry = entry

  const storage = getSessionStorage()
  if (!storage) return

  try {
    storage.setItem(cacheKey, JSON.stringify(entry))
  } catch {
    // Session storage can be unavailable; memory cache still avoids duplicate requests.
  }
}

function setNamedMeta(name, value) {
  if (typeof document === "undefined" || !value) return
  let meta = document.head.querySelector(`meta[name="${name}"]`)
  if (!meta) {
    meta = document.createElement("meta")
    meta.setAttribute("name", name)
    document.head.appendChild(meta)
  }
  meta.setAttribute("content", value)
}

function setPropertyMeta(property, value) {
  if (typeof document === "undefined" || !value) return
  let meta = document.head.querySelector(`meta[property="${property}"]`)
  if (!meta) {
    meta = document.createElement("meta")
    meta.setAttribute("property", property)
    document.head.appendChild(meta)
  }
  meta.setAttribute("content", value)
}

function applySiteSeo(site) {
  if (typeof document === "undefined") return
  const seo = site?.seo && typeof site.seo === "object" ? site.seo : {}
  if (seo.title) {
    document.title = seo.title
    setPropertyMeta("og:title", seo.title)
    setNamedMeta("twitter:title", seo.title)
  }
  if (seo.description) {
    setNamedMeta("description", seo.description)
    setPropertyMeta("og:description", seo.description)
    setNamedMeta("twitter:description", seo.description)
  }
  setPropertyMeta("og:type", "website")
  setNamedMeta("twitter:card", "summary")
}

function ensureTrackerScript(site) {
  if (typeof document === "undefined") return

  const trackerKey = String(site?.tracker_key || "").trim()
  if (!trackerKey) return

  const existing = document.getElementById(trackerScriptId)
  if (existing?.dataset?.siteKey === trackerKey) return
  if (existing) existing.remove()

  const script = document.createElement("script")
  script.id = trackerScriptId
  script.src = buildBackendUrl("tracker.js")
  script.async = true
  script.dataset.siteKey = trackerKey
  script.dataset.siteSlug = siteSlug
  document.body.appendChild(script)
}

export function toPublicMediaUrl(value) {
  const raw = String(value || "").trim()
  if (!raw) return ""
  if (/^https?:\/\//i.test(raw)) return raw
  if (raw.startsWith("/media/")) return buildBackendUrl(raw)
  return raw
}

export function hydrateMediaUrls(payload, parentKey = "") {
  if (Array.isArray(payload)) {
    return payload.map((item) => hydrateMediaUrls(item, parentKey))
  }

  if (!payload || typeof payload !== "object") {
    if (typeof payload === "string" && mediaKeyPattern.test(parentKey)) {
      return toPublicMediaUrl(payload)
    }
    return payload
  }

  const next = {}
  for (const [key, value] of Object.entries(payload)) {
    if (typeof value === "string" && mediaKeyPattern.test(key)) {
      next[key] = toPublicMediaUrl(value)
      continue
    }
    next[key] = hydrateMediaUrls(value, key)
  }
  return next
}

function normalizePayload(payload) {
  const sections = Array.isArray(payload?.sections) ? payload.sections : []
  return {
    site: payload?.site || null,
    sections: sections.map((section) => ({
      ...section,
      content: hydrateMediaUrls(section?.content || {}),
    })),
  }
}

export async function loadPublicSite({ force = false, enableTracker = false } = {}) {
  if (!force) {
    const cached = readCache()
    if (cached) {
      const normalized = normalizePayload(cached)
      applySiteSeo(normalized.site)
      if (enableTracker) ensureTrackerScript(normalized.site)
      return normalized
    }
    if (pendingRequest) {
      if (!enableTracker) return pendingRequest
      return pendingRequest.then((payload) => {
        ensureTrackerScript(payload.site)
        return payload
      })
    }
  }

  pendingRequest = fetch(buildApiUrl(`sites/${encodeURIComponent(siteSlug)}/`), {
    headers: { Accept: "application/json" },
    cache: "default",
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`public site request failed: ${response.status}`)
      }
      const payload = await response.json()
      writeCache(payload)
      const normalized = normalizePayload(payload)
      applySiteSeo(normalized.site)
      if (enableTracker) ensureTrackerScript(normalized.site)
      return normalized
    })
    .finally(() => {
      pendingRequest = null
    })

  return pendingRequest
}

export function findSection(payload, key) {
  return payload.sections.find((section) => section?.key === key) || null
}

export async function getSectionContent(key) {
  const payload = await loadPublicSite()
  return findSection(payload, key)?.content || {}
}

export function parseJsonContent(content, key = "items_json", fallback = []) {
  const raw = content?.[key]
  if (Array.isArray(raw)) return hydrateMediaUrls(raw)
  if (raw && typeof raw === "object") return hydrateMediaUrls(raw)
  if (typeof raw !== "string" || !raw.trim()) return fallback
  try {
    return hydrateMediaUrls(JSON.parse(raw))
  } catch {
    return fallback
  }
}

export async function getJsonSectionItems(sectionKey, fieldKey = "items_json") {
  const content = await getSectionContent(sectionKey)
  return parseJsonContent(content, fieldKey, [])
}
