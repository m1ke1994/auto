import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getMySiteRequest, getMySitesRequest } from '../api/site'

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
      sites.value = Array.isArray(data) ? data : []
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

  function reset() {
    sites.value = []
    currentSiteId.value = null
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
    reset,
  }
})
