import http from './http'

export const getLeadsRequest = (params = {}) => http.get('/api/admin/leads/', { params })
export const getLeadRequest = (leadId) => http.get(`/api/admin/leads/${leadId}/`)
export const patchLeadStatusRequest = (leadId, payload) => http.patch(`/api/admin/leads/${leadId}/`, payload)
export const deleteLeadRequest = (leadId) => http.delete(`/api/admin/leads/${leadId}/`)
