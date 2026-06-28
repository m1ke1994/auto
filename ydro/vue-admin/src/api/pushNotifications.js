import http from './http'

export const getPushConfigRequest = () => http.get('/api/admin/push-subscriptions/')
export const createPushSubscriptionRequest = (subscription) =>
  http.post('/api/admin/push-subscriptions/', subscription)
export const deletePushSubscriptionRequest = (endpoint) =>
  http.delete('/api/admin/push-subscriptions/', { data: { endpoint } })
