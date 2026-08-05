import { API_URL, BACKEND_URL } from '../config/env'

const TRACKNODE_SLUG = 'tracknode'
const CACHE_KEY = 'tracknode:public-site-content'
const CACHE_TTL_MS = 5 * 60 * 1000
const TRACKER_ID = 'tracknode-public-tracker'

let memoryCache = null
let pendingRequest = null

function isFresh(entry) {
  return Boolean(entry?.payload && Number.isFinite(entry.cachedAt) && Date.now() - entry.cachedAt < CACHE_TTL_MS)
}

function readCache() {
  if (isFresh(memoryCache)) return memoryCache.payload
  try {
    const entry = JSON.parse(sessionStorage.getItem(CACHE_KEY) || 'null')
    if (!isFresh(entry)) return null
    memoryCache = entry
    return entry.payload
  } catch {
    return null
  }
}

function writeCache(payload) {
  memoryCache = { payload, cachedAt: Date.now() }
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify(memoryCache))
  } catch {
    // Memory cache remains available when sessionStorage is blocked.
  }
}

function setMeta(selector, attribute, value) {
  if (!value) return
  let element = document.head.querySelector(selector)
  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(attribute[0], attribute[1])
    document.head.appendChild(element)
  }
  element.setAttribute('content', String(value))
}

function setCanonical(value) {
  if (!value) return
  let element = document.head.querySelector('link[rel="canonical"]')
  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }
  element.setAttribute('href', value)
}

function isTrackNodeTrackerScript(script) {
  const src = String(script?.src || '')
  return src.includes('/tracker.js') || src.includes('/api/mini/tracker.js')
}

function trackerScriptKey(script) {
  const dataset = script?.dataset || {}
  return String(dataset.siteKey || dataset.token || dataset.apiKey || '').trim()
}

function removeExistingTrackNodeTrackerScripts(nextKey) {
  let hasCurrentScript = false
  document.querySelectorAll('script').forEach((script) => {
    if (!isTrackNodeTrackerScript(script)) return

    const key = trackerScriptKey(script)
    if (key === nextKey && script.id === TRACKER_ID) {
      hasCurrentScript = true
      return
    }

    if (key !== nextKey || script.id === TRACKER_ID || script.dataset.tracknodeManaged === 'true') {
      script.remove()
    } else {
      hasCurrentScript = true
    }
  })

  const activeTracker = window.__trackNodeTracker
  if (activeTracker?.active !== false && activeTracker?.token && activeTracker.token !== nextKey) {
    activeTracker.destroy?.('public_site_key_changed')
  }

  return hasCurrentScript
}

export function applyPublicSiteSeo(site) {
  const seo = site?.seo && typeof site.seo === 'object' ? site.seo : {}
  const title = seo.title || seo.og_title
  const description = seo.description || seo.og_description
  const canonical = seo.canonical || window.location.href
  const ogTitle = seo.og_title || title
  const ogDescription = seo.og_description || description

  if (title) document.title = title
  setCanonical(canonical)
  setMeta('meta[name="description"]', ['name', 'description'], description)
  setMeta('meta[name="keywords"]', ['name', 'keywords'], seo.keywords)
  setMeta('meta[name="robots"]', ['name', 'robots'], seo.robots || 'index,follow')
  setMeta('meta[property="og:type"]', ['property', 'og:type'], 'website')
  setMeta('meta[property="og:title"]', ['property', 'og:title'], ogTitle)
  setMeta('meta[property="og:description"]', ['property', 'og:description'], ogDescription)
  setMeta('meta[property="og:url"]', ['property', 'og:url'], canonical)
  setMeta('meta[property="og:image"]', ['property', 'og:image'], seo.og_image)
  setMeta('meta[name="twitter:card"]', ['name', 'twitter:card'], 'summary_large_image')
  setMeta('meta[name="twitter:title"]', ['name', 'twitter:title'], ogTitle)
  setMeta('meta[name="twitter:description"]', ['name', 'twitter:description'], ogDescription)
  setMeta('meta[name="twitter:image"]', ['name', 'twitter:image'], seo.og_image)

  if (seo.structured_data && typeof seo.structured_data === 'object') {
    let script = document.head.querySelector('script[data-route-json-ld="true"]')
    if (!script) {
      script = document.createElement('script')
      script.type = 'application/ld+json'
      script.dataset.routeJsonLd = 'true'
      document.head.appendChild(script)
    }
    script.textContent = JSON.stringify(seo.structured_data)
  }
}

export function ensurePublicSiteTracker(site) {
  const trackerKey = String(site?.tracker_key || '').trim()
  if (!trackerKey) return

  if (removeExistingTrackNodeTrackerScripts(trackerKey)) return
  if (window.__trackNodeTracker?.active !== false && window.__trackNodeTracker?.token === trackerKey) return

  const script = document.createElement('script')
  script.id = TRACKER_ID
  script.src = `${BACKEND_URL}/tracker.js`
  script.async = true
  script.dataset.siteKey = trackerKey
  script.dataset.siteSlug = TRACKNODE_SLUG
  script.dataset.tracknodeManaged = 'true'
  document.body.appendChild(script)
}

export async function loadTrackNodePublicSite({ force = false } = {}) {
  if (!force) {
    const cached = readCache()
    if (cached) return cached
    if (pendingRequest) return pendingRequest
  }

  pendingRequest = fetch(`${API_URL}/sites/${TRACKNODE_SLUG}/`, {
    headers: { Accept: 'application/json' },
    credentials: 'same-origin',
  })
    .then(async (response) => {
      if (!response.ok) throw new Error(`Не удалось загрузить лендинг TrackNode (${response.status}).`)
      const payload = await response.json()
      if (!payload?.site || !Array.isArray(payload?.sections)) {
        throw new Error('Ядро вернуло некорректные данные лендинга TrackNode.')
      }
      writeCache(payload)
      return payload
    })
    .finally(() => {
      pendingRequest = null
    })

  return pendingRequest
}

export async function submitPublicSiteLead(siteSlug, payload) {
  const slug = String(siteSlug || '').trim()
  if (!slug) throw new Error('Не удалось определить сайт для заявки.')
  const response = await fetch(`${API_URL}/public/sites/${encodeURIComponent(slug)}/leads/`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    credentials: 'omit',
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const error = new Error(data?.message || 'Не удалось отправить заявку.')
    error.details = data?.errors || {}
    throw error
  }
  return data
}
