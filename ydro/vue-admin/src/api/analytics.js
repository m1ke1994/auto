import http from './http'

export const getSiteAnalyticsSummaryRequest = (siteId, params = {}) =>
  http.get(`/api/admin/my-sites/${siteId}/analytics/summary/`, { params })

export const getSiteAnalyticsSectionRequest = (siteId, section, params = {}) =>
  http.get(`/api/admin/my-sites/${siteId}/analytics/${section}/`, { params })

export const getSiteAnalyticsSessionRequest = (siteId, sessionId, params = {}) =>
  http.get(`/api/admin/my-sites/${siteId}/analytics/sessions/${encodeURIComponent(sessionId)}/`, { params })
