const defaultSiteSlug = 'a-meditation'

function runtimeMeta(name) {
  if (typeof document === 'undefined') return ''
  return document.head.querySelector(`meta[name="${name}"]`)?.content?.trim() || ''
}

const runtimeSite = typeof window !== 'undefined' && window.__TRACKNODE_SITE__
  ? window.__TRACKNODE_SITE__
  : {}

function requiredEnv(name, rawValue) {
  const value = String(rawValue || '').trim()
  if (!value) {
    throw new Error(`${name} must be set`)
  }
  return value
}

function normalizeUrl(value) {
  return String(value || '').trim().replace(/\/+$/, '')
}

export const apiUrl = normalizeUrl(requiredEnv('VITE_API_URL', import.meta.env.VITE_API_URL))
export const backendUrl = normalizeUrl(requiredEnv('VITE_BACKEND_URL', import.meta.env.VITE_BACKEND_URL))
export const publicSiteUrl = normalizeUrl(
  requiredEnv('VITE_PUBLIC_SITE_URL', import.meta.env.VITE_PUBLIC_SITE_URL || import.meta.env.VITE_SITE_URL),
)
export const siteSlug = String(runtimeSite.slug || runtimeMeta('tracknode-site-slug') || import.meta.env.VITE_SITE_SLUG || defaultSiteSlug).trim()
export const isPreviewMode = runtimeSite.preview === true || runtimeMeta('tracknode-preview-mode') === 'true'
export const previewToken = isPreviewMode ? String(runtimeSite.token || '').trim() : ''

export function buildApiUrl(path) {
  const url = `${apiUrl}/${String(path || '').replace(/^\/+/, '')}`
  if (!previewToken) return url
  const separator = url.includes('?') ? '&' : '?'
  return `${url}${separator}token=${encodeURIComponent(previewToken)}`
}

export function buildBackendUrl(path) {
  const value = String(path || '')
  if (!value || /^https?:\/\//i.test(value)) return value
  return `${backendUrl}/${value.replace(/^\/+/, '')}`
}

export function buildPublicUrl(path) {
  const value = String(path || '')
  if (!value || /^https?:\/\//i.test(value)) return value
  return `${publicSiteUrl}/${value.replace(/^\/+/, '')}`
}
