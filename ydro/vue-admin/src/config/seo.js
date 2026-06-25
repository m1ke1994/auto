import { SITE_URL } from './env'

const SITE_NAME = import.meta.env.VITE_SITE_NAME || 'TrackNode'
const SITE_DESCRIPTION =
  import.meta.env.VITE_SITE_DESCRIPTION ||
  'TrackNode объединяет аналитику сайтов, лиды, SEO-аудит и отчёты в одном кабинете.'
const OG_IMAGE_URL = import.meta.env.VITE_OG_IMAGE_URL || `${SITE_URL}/og-image.svg`

function setMeta(selector, attribute, value) {
  let element = document.head.querySelector(selector)

  if (!element) {
    element = document.createElement('meta')
    const [key, name] = attribute
    element.setAttribute(key, name)
    document.head.appendChild(element)
  }

  element.setAttribute('content', value)
}

function removeElement(selector) {
  const element = document.head.querySelector(selector)
  if (element) element.remove()
}

function setCanonical(url) {
  let element = document.head.querySelector('link[rel="canonical"]')

  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }

  element.setAttribute('href', url)
}

function setJsonLd(value) {
  const selector = 'script[data-route-json-ld="true"]'
  if (!value) {
    removeElement(selector)
    return
  }

  let element = document.head.querySelector(selector)
  if (!element) {
    element = document.createElement('script')
    element.setAttribute('type', 'application/ld+json')
    element.setAttribute('data-route-json-ld', 'true')
    document.head.appendChild(element)
  }

  element.textContent = JSON.stringify(value)
}

export function applyRouteSeo(route) {
  const routeTitle = route.meta.title
  const title = route.meta.seoTitle || (routeTitle ? `${routeTitle} | ${SITE_NAME}` : `${SITE_NAME} — аналитика, лиды и SEO-аудит`)
  const description = route.meta.description || SITE_DESCRIPTION
  const canonicalUrl = route.meta.canonicalUrl || `${SITE_URL}${route.path === '/' ? '/' : route.path}`
  const robots = route.meta.public ? 'index,follow' : 'noindex,nofollow'
  const ogType = route.meta.ogType || 'website'
  const twitterCard = route.meta.twitterCard || 'summary_large_image'

  document.title = title
  setCanonical(canonicalUrl)
  setMeta('meta[name="description"]', ['name', 'description'], description)
  if (route.meta.keywords) {
    setMeta('meta[name="keywords"]', ['name', 'keywords'], route.meta.keywords)
  } else {
    removeElement('meta[name="keywords"]')
  }
  setMeta('meta[name="robots"]', ['name', 'robots'], robots)
  setMeta('meta[property="og:type"]', ['property', 'og:type'], ogType)
  setMeta('meta[property="og:title"]', ['property', 'og:title'], title)
  setMeta(
    'meta[property="og:description"]',
    ['property', 'og:description'],
    description,
  )
  setMeta('meta[property="og:url"]', ['property', 'og:url'], canonicalUrl)
  setMeta('meta[property="og:image"]', ['property', 'og:image'], OG_IMAGE_URL)
  setMeta('meta[name="twitter:card"]', ['name', 'twitter:card'], twitterCard)
  setMeta('meta[name="twitter:title"]', ['name', 'twitter:title'], title)
  setMeta(
    'meta[name="twitter:description"]',
    ['name', 'twitter:description'],
    description,
  )
  setMeta(
    'meta[name="twitter:image"]',
    ['name', 'twitter:image'],
    OG_IMAGE_URL,
  )
  setJsonLd(route.meta.jsonLd)
}
