import http from './http'

export const getNewsRequest = () => http.get('/api/client/news/')
export const getNewsDetailRequest = (newsId) => http.get(`/api/client/news/${newsId}/`)
export const markNewsReadRequest = (newsId) => http.post(`/api/client/news/${newsId}/read/`)
export const getUnreadNewsCountRequest = () => http.get('/api/client/news/unread-count/')

