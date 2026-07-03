import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  getNewsDetailRequest,
  getNewsRequest,
  getUnreadNewsCountRequest,
  markNewsReadRequest,
} from '../api/news'
import { getServiceWorkerRegistration } from '../pwa'

const POLLING_INTERVAL = 60_000

export const useNewsStore = defineStore('news', () => {
  const items = ref([])
  const currentNews = ref(null)
  const unreadCount = ref(0)
  const loading = ref(false)
  const detailLoading = ref(false)
  const error = ref('')
  const toast = ref(null)
  const browserPermission = ref(
    typeof Notification === 'undefined' ? 'unsupported' : Notification.permission,
  )

  let pollingTimer
  let toastTimer
  let initialized = false

  const hasUnread = computed(() => unreadCount.value > 0)

  function normalizeList(payload) {
    if (Array.isArray(payload)) return payload
    return Array.isArray(payload?.results) ? payload.results : []
  }

  function showToast(title, body) {
    window.clearTimeout(toastTimer)
    toast.value = { title, body }
    toastTimer = window.setTimeout(() => {
      toast.value = null
    }, 8_000)
  }

  function dismissToast() {
    window.clearTimeout(toastTimer)
    toast.value = null
  }

  async function showBrowserNotification() {
    if (typeof Notification === 'undefined' || Notification.permission !== 'granted') return

    const options = {
      body: 'Нажмите, чтобы открыть раздел уведомлений.',
      icon: '/pwa-icon-192.svg',
      badge: '/pwa-icon-192.svg',
      tag: 'tracknode-dashboard-news',
      data: { url: '/dashboard/notifications' },
    }

    try {
      const registration = await getServiceWorkerRegistration()
      await registration.showNotification('Новая новость TrackNode', options)
    } catch {
      try {
        const notification = new Notification('Новая новость TrackNode', options)
        notification.onclick = () => {
          window.focus()
          window.location.assign('/dashboard/notifications')
        }
      } catch {
        // Badge and in-app toast remain available when system notifications fail.
      }
    }
  }

  async function fetchUnreadCount({ notifyOnIncrease = true } = {}) {
    const previous = unreadCount.value
    try {
      const { data } = await getUnreadNewsCountRequest()
      const next = Math.max(0, Number(data?.count) || 0)
      unreadCount.value = next

      if (initialized && notifyOnIncrease && next > previous) {
        const added = next - previous
        showToast(
          'Новая новость TrackNode',
          added > 1 ? `Появилось новых новостей: ${added}` : 'Нажмите, чтобы открыть.',
        )
        showBrowserNotification()
      }
      initialized = true
      return next
    } catch (requestError) {
      if (!initialized) unreadCount.value = 0
      throw requestError
    }
  }

  async function fetchNews() {
    loading.value = true
    error.value = ''
    try {
      const { data } = await getNewsRequest()
      items.value = normalizeList(data)
      return items.value
    } catch (requestError) {
      error.value = requestError?.response?.data?.detail || 'Не удалось загрузить новости.'
      throw requestError
    } finally {
      loading.value = false
    }
  }

  async function fetchNewsDetail(newsId) {
    detailLoading.value = true
    error.value = ''
    currentNews.value = null
    try {
      const { data } = await getNewsDetailRequest(newsId)
      currentNews.value = data
      return data
    } catch (requestError) {
      error.value = requestError?.response?.status === 404
        ? 'Новость не найдена или ещё не опубликована.'
        : requestError?.response?.data?.detail || 'Не удалось загрузить новость.'
      throw requestError
    } finally {
      detailLoading.value = false
    }
  }

  async function markRead(newsId) {
    const target = items.value.find((item) => item.id === Number(newsId))
    if (target?.is_read || (currentNews.value?.id === Number(newsId) && currentNews.value.is_read)) return

    const { data } = await markNewsReadRequest(newsId)
    if (target) Object.assign(target, { is_read: true, read_at: data.read_at })
    if (currentNews.value?.id === Number(newsId)) {
      Object.assign(currentNews.value, { is_read: true, read_at: data.read_at })
    }
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    return data
  }

  async function requestBrowserPermission() {
    if (typeof Notification === 'undefined') {
      browserPermission.value = 'unsupported'
      return browserPermission.value
    }
    browserPermission.value = await Notification.requestPermission()
    if (browserPermission.value === 'granted') {
      showToast('Системные уведомления включены', 'Новые новости TrackNode будут появляться в браузере.')
    }
    return browserPermission.value
  }

  function startPolling() {
    stopPolling()
    fetchUnreadCount({ notifyOnIncrease: false }).catch(() => {})
    pollingTimer = window.setInterval(() => {
      fetchUnreadCount().catch(() => {})
    }, POLLING_INTERVAL)
  }

  function stopPolling() {
    window.clearInterval(pollingTimer)
    pollingTimer = undefined
  }

  function reset() {
    stopPolling()
    dismissToast()
    items.value = []
    currentNews.value = null
    unreadCount.value = 0
    error.value = ''
    initialized = false
  }

  return {
    items,
    currentNews,
    unreadCount,
    loading,
    detailLoading,
    error,
    toast,
    browserPermission,
    hasUnread,
    fetchUnreadCount,
    fetchNews,
    fetchNewsDetail,
    markRead,
    requestBrowserPermission,
    startPolling,
    stopPolling,
    dismissToast,
    reset,
  }
})
