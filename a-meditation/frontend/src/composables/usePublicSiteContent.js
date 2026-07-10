import { computed, onMounted, ref } from 'vue'

import { buildApiUrl, buildBackendUrl, buildPublicUrl, siteSlug } from '../config/api'

const mediaKeyPattern = /(image|video|avatar|poster|photo|src|file)$/i
const siteContentCacheTtlMs = 5 * 60 * 1000
const siteContentCacheKey = `public-site-content:${siteSlug}`
const trackerScriptId = 'yadro-analytics-tracker'

let memoryCacheEntry = null
let pendingSiteContentRequest = null

function isFreshCacheEntry(entry) {
  return Boolean(
    entry?.payload &&
    Number.isFinite(entry.cachedAt) &&
    Date.now() - entry.cachedAt < siteContentCacheTtlMs,
  )
}

function getSessionStorage() {
  if (typeof window === 'undefined') return null

  try {
    return window.sessionStorage
  } catch {
    return null
  }
}

function readSessionCacheEntry() {
  const storage = getSessionStorage()
  if (!storage) return null

  try {
    return JSON.parse(storage.getItem(siteContentCacheKey) || 'null')
  } catch {
    return null
  }
}

function readCachedPayload() {
  if (isFreshCacheEntry(memoryCacheEntry)) {
    return memoryCacheEntry.payload
  }

  const sessionEntry = readSessionCacheEntry()
  if (!isFreshCacheEntry(sessionEntry)) return null

  memoryCacheEntry = sessionEntry
  return sessionEntry.payload
}

function writeCachedPayload(payload) {
  const entry = {
    cachedAt: Date.now(),
    payload,
  }

  memoryCacheEntry = entry

  const storage = getSessionStorage()
  if (!storage) return

  try {
    storage.setItem(siteContentCacheKey, JSON.stringify(entry))
  } catch {
    // Storage may be unavailable in private mode; memory cache still helps this tab.
  }
}

function absolutizeMediaValue(value) {
  if (typeof value !== 'string') return value
  if (value.startsWith('/media/')) return buildBackendUrl(value)
  return value
}

function hydrateMediaUrls(payload) {
  if (Array.isArray(payload)) {
    return payload.map((item) => hydrateMediaUrls(item))
  }

  if (!payload || typeof payload !== 'object') {
    return payload
  }

  const next = {}
  for (const [key, value] of Object.entries(payload)) {
    if (typeof value === 'string' && mediaKeyPattern.test(key)) {
      next[key] = absolutizeMediaValue(value)
      continue
    }
    next[key] = hydrateMediaUrls(value)
  }
  return next
}

function setMetaDescription(value) {
  if (!value) return

  setNamedMeta('description', value)
}

function setNamedMeta(name, value) {
  if (!value) return

  let meta = document.head.querySelector(`meta[name="${name}"]`)
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('name', name)
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', value)
}

function setPropertyMeta(property, value) {
  if (!value) return

  let meta = document.head.querySelector(`meta[property="${property}"]`)
  if (!meta) {
    meta = document.createElement('meta')
    meta.setAttribute('property', property)
    document.head.appendChild(meta)
  }
  meta.setAttribute('content', value)
}

function setCanonicalLink(value) {
  if (!value) return

  let link = document.head.querySelector('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.setAttribute('rel', 'canonical')
    document.head.appendChild(link)
  }
  link.setAttribute('href', value)
}

function setJsonLd(value) {
  if (!value) return

  let script = document.getElementById('public-site-json-ld')
  if (!script) {
    script = document.createElement('script')
    script.id = 'public-site-json-ld'
    script.type = 'application/ld+json'
    document.head.appendChild(script)
  }

  script.textContent = typeof value === 'string' ? value : JSON.stringify(value)
}

function absolutizeSeoUrl(value) {
  if (typeof value !== 'string' || !value.trim()) return ''
  const trimmed = value.trim()
  if (/^https?:\/\//i.test(trimmed)) return trimmed
  if (trimmed.startsWith('/media/')) return buildBackendUrl(trimmed)
  return buildPublicUrl(trimmed)
}

function firstSeoValue(seo, keys) {
  for (const key of keys) {
    const value = seo?.[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return ''
}

function applySiteSeo(site) {
  const seo = site?.seo
  if (!seo || typeof seo !== 'object') return

  const title = firstSeoValue(seo, ['title', 'og_title', 'twitter_title'])
  const description = firstSeoValue(seo, ['description', 'og_description', 'twitter_description'])
  const siteName = firstSeoValue(seo, ['site_name', 'og_site_name']) || site?.name || 'Leelabird'
  const canonical = absolutizeSeoUrl(firstSeoValue(seo, ['canonical', 'url', 'og_url']) || '/')
  const image = absolutizeSeoUrl(firstSeoValue(seo, ['image', 'og_image', 'twitter_image']))
  const ogTitle = firstSeoValue(seo, ['og_title']) || title
  const ogDescription = firstSeoValue(seo, ['og_description']) || description
  const twitterTitle = firstSeoValue(seo, ['twitter_title']) || title
  const twitterDescription = firstSeoValue(seo, ['twitter_description']) || description
  const twitterCard = firstSeoValue(seo, ['twitter_card']) || (image ? 'summary_large_image' : 'summary')

  if (title) {
    document.title = title
  }

  setMetaDescription(description)
  setPropertyMeta('og:type', 'website')
  setPropertyMeta('og:site_name', siteName)
  setPropertyMeta('og:title', ogTitle)
  setPropertyMeta('og:description', ogDescription)
  setPropertyMeta('og:url', canonical)
  setPropertyMeta('og:image', image)
  setNamedMeta('twitter:card', twitterCard)
  setNamedMeta('twitter:title', twitterTitle)
  setNamedMeta('twitter:description', twitterDescription)
  setNamedMeta('twitter:image', image)
  setCanonicalLink(canonical)
  setJsonLd(seo.json_ld)
}

function ensureTrackerScript(site) {
  if (typeof document === 'undefined') return

  const trackerKey = String(site?.tracker_key || '').trim()
  if (!trackerKey) return

  const existing = document.getElementById(trackerScriptId)
  if (existing?.dataset?.siteKey === trackerKey) return

  if (existing) {
    existing.remove()
  }

  const script = document.createElement('script')
  script.id = trackerScriptId
  script.src = buildBackendUrl('tracker.js')
  script.async = true
  script.dataset.siteKey = trackerKey
  script.dataset.siteSlug = siteSlug
  document.body.appendChild(script)
}

function normalizePayload(payload) {
  const rawSections = Array.isArray(payload?.sections) ? payload.sections : []

  return {
    site: payload?.site || null,
    sections: rawSections.map((section) => ({
      ...section,
      content: hydrateMediaUrls(section?.content || {}),
    })),
  }
}

async function fetchSiteContent(force = false) {
  if (!force) {
    const cachedPayload = readCachedPayload()
    if (cachedPayload) return cachedPayload

    if (pendingSiteContentRequest) return pendingSiteContentRequest
  }

  pendingSiteContentRequest = fetch(buildApiUrl(`sites/${encodeURIComponent(siteSlug)}/`), {
    cache: 'default',
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to load site content: ${response.status}`)
      }

      const payload = await response.json()
      writeCachedPayload(payload)
      return payload
    })
    .finally(() => {
      pendingSiteContentRequest = null
    })

  return pendingSiteContentRequest
}

export function usePublicSiteContent() {
  const site = ref(null)
  const sections = ref([])
  const loading = ref(false)
  const error = ref('')

  const sectionsByKey = computed(() => {
    const map = {}
    for (const section of sections.value) {
      if (!section?.key) continue
      map[section.key] = section
    }
    return map
  })

  const getSection = (key) => sectionsByKey.value[key] || null

  const loadSiteContent = async ({ force = false } = {}) => {
    const cachedPayload = !force ? readCachedPayload() : null
    if (cachedPayload) {
      const normalized = normalizePayload(cachedPayload)
      site.value = normalized.site
      sections.value = normalized.sections
      applySiteSeo(site.value)
      ensureTrackerScript(site.value)
      loading.value = false
      error.value = ''
      return
    }

    loading.value = true
    error.value = ''

    try {
      const payload = await fetchSiteContent(force)
      const normalized = normalizePayload(payload)
      site.value = normalized.site
      applySiteSeo(site.value)
      ensureTrackerScript(site.value)
      sections.value = normalized.sections
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to load site content'
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    loadSiteContent()
  })

  return {
    site,
    sections,
    sectionsByKey,
    loading,
    error,
    getSection,
    reload: () => loadSiteContent({ force: true }),
  }
}
