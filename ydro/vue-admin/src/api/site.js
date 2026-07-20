import http from './http'

export const getMySitesRequest = () => http.get('/api/admin/my-sites/')
export const getMySiteRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/`)
export const getSiteTemplateCatalogRequest = (category = '') => http.get('/api/website-templates/', { params: category ? { category } : {} })
export const createSiteFromTemplateRequest = (payload, config = {}) => http.post(`/api/website-templates/${encodeURIComponent(payload.template_slug)}/create-site/`, payload, config)
export const generateSiteFromCategoryRequest = (payload, config = {}) => http.post('/api/website-templates/generate/', payload, config)
export const regenerateSiteDesignRequest = (siteId, payload, config = {}) => http.post(`/api/sites/${siteId}/regenerate-design/`, payload, config)
export const getSiteTelegramRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/telegram/`)
export const sendSiteTelegramTestRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/telegram/test/`, {})
export const disconnectSiteTelegramRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/telegram/disconnect/`, {})
export const refreshSiteTrackingKeyRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/tracking-key/refresh/`, {})
