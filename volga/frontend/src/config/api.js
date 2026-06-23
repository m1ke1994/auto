const defaultSiteSlug = "novoe-konakovo"

function normalizeUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "")
}

export const apiUrl = normalizeUrl(import.meta.env.VITE_API_URL || "/api")
export const backendUrl = normalizeUrl(import.meta.env.VITE_BACKEND_URL || "")
export const siteSlug = String(import.meta.env.VITE_SITE_SLUG || defaultSiteSlug).trim()
export const siteUrl = normalizeUrl(import.meta.env.VITE_SITE_URL || "")
export const publicSiteUrl = normalizeUrl(import.meta.env.VITE_PUBLIC_SITE_URL || siteUrl || "")

export function buildApiUrl(path) {
  const normalizedPath = String(path || "").replace(/^\/+/, "")
  return `${apiUrl}/${normalizedPath}`
}

export function buildBackendUrl(path) {
  const value = String(path || "")
  if (!value || /^https?:\/\//i.test(value)) return value
  const normalizedPath = value.replace(/^\/+/, "")
  if (!backendUrl) return `/${normalizedPath}`
  return `${backendUrl}/${normalizedPath}`
}
