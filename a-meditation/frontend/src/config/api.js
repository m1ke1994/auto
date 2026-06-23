const defaultSiteSlug = 'a-meditation'

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
export const siteSlug = String(import.meta.env.VITE_SITE_SLUG || defaultSiteSlug).trim()

export function buildApiUrl(path) {
  return `${apiUrl}/${String(path || '').replace(/^\/+/, '')}`
}

export function buildBackendUrl(path) {
  const value = String(path || '')
  if (!value || /^https?:\/\//i.test(value)) return value
  return `${backendUrl}/${value.replace(/^\/+/, '')}`
}
