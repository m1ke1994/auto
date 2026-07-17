import http from './http'

export const getMySitesRequest = () => http.get('/api/admin/my-sites/')
export const getMySiteRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/`)
export const getSiteTemplateCatalogRequest = (category = '') => http.get('/api/admin/site-templates/', { params: category ? { category } : {} })
export const createSiteFromTemplateRequest = (payload, config = {}) => http.post('/api/admin/site-templates/create-site/', payload, config)
export const getSiteTelegramRequest = (siteId) => http.get(`/api/admin/my-sites/${siteId}/telegram/`)
export const sendSiteTelegramTestRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/telegram/test/`, {})
export const disconnectSiteTelegramRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/telegram/disconnect/`, {})
export const refreshSiteTrackingKeyRequest = (siteId) => http.post(`/api/admin/my-sites/${siteId}/tracking-key/refresh/`, {})
