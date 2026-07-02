const CACHE_PREFIX = 'tracknode-dashboard-'
const CACHE_NAME = `${CACHE_PREFIX}v3`
const STATIC_CACHE_NAME = `${CACHE_NAME}-static`
const PAGE_CACHE_NAME = `${CACHE_NAME}-pages`
const CACHE_NAMES = new Set([STATIC_CACHE_NAME, PAGE_CACHE_NAME])
const APP_SHELL_ROUTES = ['/', '/dashboard', '/login', '/billing']
const STATIC_PATHS = [
  '/manifest.webmanifest',
  '/pwa-icon-192.svg',
  '/pwa-icon-512.svg',
  '/favicon.svg',
]

function isExcludedPath(pathname) {
  return (
    pathname === '/api' ||
    pathname.startsWith('/api/') ||
    pathname === '/admin' ||
    pathname.startsWith('/admin/') ||
    pathname.startsWith('/media/') ||
    pathname.startsWith('/static/')
  )
}

function isHtmlResponse(response) {
  return Boolean(
    response?.ok &&
    response.type === 'basic' &&
    response.headers.get('content-type')?.includes('text/html'),
  )
}

function isCacheableAsset(response) {
  return Boolean(
    response?.ok &&
    response.type === 'basic' &&
    !response.headers.get('content-type')?.includes('text/html'),
  )
}

function assetPathsFromHtml(html) {
  const paths = new Set()
  const pattern = /(?:src|href)=["'](\/assets\/[^"'#?]+(?:\?[^"']*)?)["']/g
  for (const match of html.matchAll(pattern)) paths.add(match[1])
  return [...paths]
}

async function fetchForCache(path) {
  return fetch(new Request(path, { cache: 'reload', credentials: 'same-origin' }))
}

async function precacheAppShell() {
  const shellResponse = await fetchForCache('/dashboard')
  if (!isHtmlResponse(shellResponse)) {
    throw new Error('TrackNode app shell did not return HTML.')
  }

  const html = await shellResponse.clone().text()
  const pageCache = await caches.open(PAGE_CACHE_NAME)
  await Promise.all(
    APP_SHELL_ROUTES.map((path) => pageCache.put(path, shellResponse.clone())),
  )

  const staticCache = await caches.open(STATIC_CACHE_NAME)
  const requiredAssets = assetPathsFromHtml(html)
  await Promise.all(
    requiredAssets.map(async (path) => {
      const response = await fetchForCache(path)
      if (!isCacheableAsset(response)) {
        throw new Error(`TrackNode asset could not be cached: ${path}`)
      }
      await staticCache.put(path, response)
    }),
  )

  await Promise.allSettled(
    STATIC_PATHS.map(async (path) => {
      const response = await fetchForCache(path)
      if (response.ok && response.type === 'basic') await staticCache.put(path, response)
    }),
  )
}

self.addEventListener('install', (event) => {
  // Do not activate a new worker until its HTML and hashed JS/CSS are cached.
  // If precaching fails, the previous working service worker remains active.
  event.waitUntil(precacheAppShell().then(() => self.skipWaiting()))
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((names) => Promise.all(
        names
          .filter((name) => name.startsWith(CACHE_PREFIX) && !CACHE_NAMES.has(name))
          .map((name) => caches.delete(name)),
      )),
      self.clients.claim(),
    ]),
  )
})

function offlineDocument() {
  return new Response(
    '<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TrackNode</title><body style="margin:0;font:16px system-ui;background:#fafbff;color:#17223b"><main style="min-height:100vh;display:grid;place-content:center;padding:24px;text-align:center"><h1>TrackNode временно недоступен</h1><p>Проверьте подключение к интернету и попробуйте открыть приложение снова.</p></main></body></html>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
  )
}

async function navigationNetworkFirst(request) {
  const cache = await caches.open(PAGE_CACHE_NAME)
  try {
    const response = await fetch(request)
    if (!isHtmlResponse(response)) throw new Error('Navigation did not return application HTML.')
    await cache.put(request, response.clone())
    return response
  } catch {
    return (
      await cache.match(request, { ignoreSearch: true }) ||
      await cache.match('/dashboard') ||
      await cache.match('/') ||
      offlineDocument()
    )
  }
}

async function cacheFirstAsset(request) {
  const cache = await caches.open(STATIC_CACHE_NAME)
  const cached = await cache.match(request, { ignoreSearch: false })
  if (cached) return cached

  const response = await fetch(request)
  if (isCacheableAsset(response)) await cache.put(request, response.clone())
  return response
}

async function networkFirstStatic(request) {
  const cache = await caches.open(STATIC_CACHE_NAME)
  try {
    const response = await fetch(request)
    if (response.ok && response.type === 'basic') await cache.put(request, response.clone())
    return response
  } catch {
    return cache.match(request)
  }
}

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin || isExcludedPath(url.pathname)) return

  if (request.mode === 'navigate') {
    event.respondWith(navigationNetworkFirst(request))
    return
  }

  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(cacheFirstAsset(request))
    return
  }

  if (STATIC_PATHS.includes(url.pathname)) {
    event.respondWith(networkFirstStatic(request))
  }
})

self.addEventListener('push', (event) => {
  let payload = {}
  try {
    payload = event.data?.json() || {}
  } catch {
    payload = { body: event.data?.text() || 'В TrackNode появилась новая заявка.' }
  }

  const title = payload.title || 'Новая заявка в TrackNode'
  const options = {
    body: payload.body || 'Откройте дашборд, чтобы посмотреть детали.',
    icon: payload.icon || '/pwa-icon-192.svg',
    badge: payload.badge || '/pwa-icon-192.svg',
    tag: payload.tag || 'tracknode-new-lead',
    data: payload.data || { url: '/dashboard' },
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  let targetUrl = new URL('/dashboard', self.location.origin)
  try {
    const requestedUrl = new URL(event.notification.data?.url || '/dashboard', self.location.origin)
    if (requestedUrl.origin === self.location.origin) targetUrl = requestedUrl
  } catch {
    // Keep the safe dashboard fallback.
  }

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(async (clients) => {
      const existingClient = clients.find((client) => new URL(client.url).origin === self.location.origin)
      if (existingClient) {
        await existingClient.navigate(targetUrl.href)
        return existingClient.focus()
      }
      return self.clients.openWindow(targetUrl.href)
    }),
  )
})
