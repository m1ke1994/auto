import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  clearSiteAnalyticsRequest,
  deleteMySiteRequest,
  getMySiteRequest,
  getMySitesRequest,
} from '../api/site'

const CURRENT_SITE_STORAGE_KEYS = ['current_site_id', 'currentSiteId', 'selected_site_id', 'selectedSiteId']

export function isClientManageableSite(site) {
  if (!site) return false
  return site.is_technical_template_source !== true
}

function normalizeSites(data) {
  return (Array.isArray(data) ? data : []).filter(isClientManageableSite)
}

export const useSiteStore = defineStore('site', () => {
  const sites = ref([])
  const currentSiteId = ref(null)
  const loading = ref(false)
  const loaded = ref(false)
  const error = ref(null)

  const currentSite = computed(() => sites.value.find((site) => site.id === currentSiteId.value) || null)

  async function fetchSites() {
    loading.value = true
    error.value = null
    try {
      const { data } = await getMySitesRequest()
      sites.value = normalizeSites(data)
      if (currentSiteId.value && !sites.value.some((site) => site.id === currentSiteId.value)) {
        currentSiteId.value = null
      }
      if (sites.value.length === 1) {
        currentSiteId.value = sites.value[0].id
      }
      loaded.value = true
      return sites.value
    } catch (fetchError) {
      error.value = fetchError
      throw fetchError
    } finally {
      loading.value = false
    }
  }

  async function fetchSite(siteId) {
    const id = Number(siteId)
    const { data } = await getMySiteRequest(id)
    if (!isClientManageableSite(data)) {
      sites.value = sites.value.filter((site) => site.id !== id)
      if (currentSiteId.value === id) currentSiteId.value = sites.value[0]?.id ?? null
      const error = new Error('Site was not found.')
      error.response = { status: 404, data: { detail: 'Site was not found.' } }
      throw error
    }
    const index = sites.value.findIndex((site) => site.id === data.id)

    if (index >= 0) {
      sites.value[index] = data
    } else {
      sites.value.push(data)
    }

    currentSiteId.value = data.id
    return data
  }

  function selectSite(siteId) {
    currentSiteId.value = Number(siteId)
  }

  async function clearSiteAnalytics(siteId, confirmation) {
    const id = Number(siteId)
    const { data } = await clearSiteAnalyticsRequest(id, confirmation)
    return data
  }

  async function deleteSite(siteId, confirmation) {
    const id = Number(siteId)
    const { data } = await deleteMySiteRequest(id, confirmation)
    sites.value = sites.value.filter((site) => site.id !== id)
    clearDeletedSiteFromStorage(id)

    if (currentSiteId.value === id) {
      currentSiteId.value = sites.value[0]?.id ?? null
    }

    loaded.value = true
    return data
  }

  function clearDeletedSiteFromStorage(siteId) {
    const id = String(siteId)
    CURRENT_SITE_STORAGE_KEYS.forEach((key) => {
      if (localStorage.getItem(key) === id) {
        localStorage.removeItem(key)
      }
    })
  }

  function reset() {
    sites.value = []
    currentSiteId.value = null
    loading.value = false
    loaded.value = false
    error.value = null
  }

  return {
    sites,
    currentSiteId,
    currentSite,
    loading,
    loaded,
    error,
    fetchSites,
    fetchSite,
    selectSite,
    clearSiteAnalytics,
    deleteSite,
    reset,
  }
})
