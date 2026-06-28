const CACHE_NAME = 'tracknode-dashboard-v1'
const STATIC_CACHE_NAME = `${CACHE_NAME}-static`
const PAGE_CACHE_NAME = `${CACHE_NAME}-pages`
const CACHE_NAMES = new Set([STATIC_CACHE_NAME, PAGE_CACHE_NAME])
const STATIC_PATHS = new Set([
  '/manifest.webmanifest',
  '/pwa-icon-192.svg',
  '/pwa-icon-512.svg',
  '/favicon.svg',
])

function isDashboardPath(pathname) {
  return (
    pathname === '/dashboard' ||
    pathname === '/login' ||
    pathname === '/mini' ||
    pathname.startsWith('/mini/') ||
    pathname.startsWith('/sites/')
  )
}

self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((names) => Promise.all(names.filter((name) => !CACHE_NAMES.has(name)).map((name) => caches.delete(name)))),
      self.clients.claim(),
    ]),
  )
})

async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName)
  try {
    const response = await fetch(request)
    if (response.ok && response.type === 'basic') await cache.put(request, response.clone())
    return response
  } catch (error) {
    const cached = await cache.match(request)
    if (cached) return cached
    if (request.mode === 'navigate') {
      const dashboard = await cache.match('/dashboard')
      if (dashboard) return dashboard
      const landing = await cache.match('/')
      if (landing) return landing
    }
    throw error
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(STATIC_CACHE_NAME)
  const cached = await cache.match(request)
  if (cached) return cached
  const response = await fetch(request)
  if (response.ok && response.type === 'basic') await cache.put(request, response.clone())
  return response
}

self.addEventListener('fetch', (event) => {
  const request = event.request
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  if (request.mode === 'navigate' && isDashboardPath(url.pathname)) {
    event.respondWith(networkFirst(request, PAGE_CACHE_NAME))
    return
  }

  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(cacheFirst(request))
    return
  }

  if (STATIC_PATHS.has(url.pathname)) {
    event.respondWith(networkFirst(request, STATIC_CACHE_NAME))
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
