import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { miniSubscriptionStatus } from '../api/mini'

const FULL_FEATURES = [
  'dashboard_overview',
  'site_edit',
  'leads',
  'notifications',
  'analytics',
  'seo_audit',
  'competitors',
  'telegram',
  'reports',
  'heatmaps',
  'session_recordings',
  'ai_recommendations',
  'billing',
  'billing_full_access',
]

const BASE_FEATURES = ['dashboard_overview', 'notifications', 'billing']

export const useAccessStore = defineStore('access', () => {
  const subscription = ref(null)
  const allowedFeatures = ref([])
  const loaded = ref(false)
  const loading = ref(false)
  const error = ref('')
  let requestPromise

  const planCode = computed(() => subscription.value?.plan_code || null)
  const planTitle = computed(() => subscription.value?.plan_title || null)
  const isBusinessAnalytics = computed(() => planCode.value === 'business_analytics')

  function normalizeFeatures(data) {
    if (Array.isArray(data?.allowed_features)) return data.allowed_features
    if (data?.plan_code === 'business_analytics' || data?.plan === 'business_analytics') return FULL_FEATURES
    if (data?.plan_code === 'content_hosting' || data?.plan === 'content_hosting') {
      return ['dashboard_overview', 'site_edit', 'leads', 'notifications', 'billing']
    }
    return BASE_FEATURES
  }

  function can(feature) {
    return !feature || allowedFeatures.value.includes(feature)
  }

  function applyAccess(data) {
    subscription.value = data
    allowedFeatures.value = normalizeFeatures(data)
    loaded.value = true
    return data
  }

  async function fetchAccess({ force = false, timeout = 4000 } = {}) {
    if (!force && loaded.value) return subscription.value
    if (requestPromise) return requestPromise

    loading.value = true
    error.value = ''
    requestPromise = miniSubscriptionStatus({ timeout })
      .then((data) => {
        return applyAccess(data)
      })
      .catch((requestError) => {
        error.value = requestError?.response?.data?.detail || 'Не удалось проверить доступ по тарифу.'
        throw requestError
      })
      .finally(() => {
        loading.value = false
        requestPromise = undefined
      })
    return requestPromise
  }

  function reset() {
    subscription.value = null
    allowedFeatures.value = []
    loaded.value = false
    loading.value = false
    error.value = ''
    requestPromise = undefined
  }

  return {
    subscription,
    allowedFeatures,
    loaded,
    loading,
    error,
    planCode,
    planTitle,
    isBusinessAnalytics,
    can,
    applyAccess,
    fetchAccess,
    reset,
  }
})
