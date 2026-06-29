import http from './http'

export const loginRequest = (payload) => http.post('/api/auth/token/', payload)
export const registerRequest = (payload) => http.post('/api/auth/register/', payload)
export const meRequest = () => http.get('/api/auth/me/')
