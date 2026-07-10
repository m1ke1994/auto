import http from './http'

const get = (path, params = {}) => http.get(`/api/platform/${path}/`, { params })
export const getPlatformOverview = (params) => get('overview', params)
export const getPlatformSites = (params) => get('sites', params)
export const getPlatformSite = (id, params) => get(`sites/${id}`, params)
export const getPlatformAnalytics = (params) => get('analytics', params)
export const getPlatformClients = (params) => get('clients', params)
export const getPlatformClient = (id) => get(`clients/${id}`)
export const getPlatformLeads = (params) => get('leads', params)
export const getPlatformRecommendations = (params) => get('recommendations', params)
export const getPlatformRecommendation = (id) => get(`recommendations/${id}`)
export const actOnPlatformRecommendation = (id, action) => http.post(`/api/platform/recommendations/${id}/`, { action })
export const getPlatformSeo = (params) => get('seo', params)
export const getPlatformSubscriptions = (params) => get('subscriptions', params)
export const getPlatformHealth = (params) => get('health', params)
export const getPlatformAudit = (params) => get('audit', params)

