import http from './http'

const base = '/api/client/ai-recommendations/'
export const listAIRecommendationJobs = () => http.get(base)
export const createAIRecommendationJob = (payload) => http.post(base, payload)
export const getAIRecommendationJob = (id) => http.get(`${base}${id}/`)
export const retryAIRecommendationJob = (id) => http.post(`${base}${id}/retry/`)
export const deleteAIRecommendationJob = (id) => http.delete(`${base}${id}/`)

