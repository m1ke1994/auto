import http from './http'

export async function getCompetitorAnalyses(siteId) {
  const { data } = await http.get(`/api/admin/sites/${siteId}/competitors/`)
  return data
}

export async function createCompetitorAnalysis(siteId, competitors) {
  const { data } = await http.post(`/api/admin/sites/${siteId}/competitors/analyze/`, { competitors })
  return data
}

export async function getCompetitorAnalysis(siteId, analysisId) {
  const { data } = await http.get(`/api/admin/sites/${siteId}/competitors/${analysisId}/`)
  return data
}

export async function downloadCompetitorAnalysisPdf(siteId, analysisId) {
  const response = await http.get(`/api/admin/sites/${siteId}/competitors/${analysisId}/pdf/`, {
    responseType: 'blob',
  })
  return response.data
}
