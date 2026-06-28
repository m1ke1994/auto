<script setup>
import { computed, onMounted, ref } from 'vue'
import { Bell, BellOff, LoaderCircle } from '@lucide/vue'

import {
  createPushSubscriptionRequest,
  deletePushSubscriptionRequest,
  getPushConfigRequest,
} from '../api/pushNotifications'
import { getServiceWorkerRegistration, supportsPushNotifications } from '../pwa'

const state = ref('loading')
const error = ref('')
const publicKey = ref('')
const registration = ref(null)
const subscription = ref(null)

const busy = computed(() => state.value === 'loading' || state.value === 'enabling' || state.value === 'disabling')
const enabled = computed(() => state.value === 'enabled')
const canEnable = computed(() => ['disabled', 'error'].includes(state.value))
const canDisable = computed(() => state.value === 'enabled')
const canRetry = computed(() => state.value === 'error')

const statusText = computed(() => {
  const labels = {
    loading: 'Проверяем состояние уведомлений…',
    enabling: 'Включаем уведомления…',
    disabling: 'Отключаем уведомления…',
    enabled: 'Уведомления включены',
    disabled: 'Уведомления отключены',
    blocked: 'Уведомления заблокированы в настройках браузера',
    unsupported: 'Этот браузер не поддерживает push-уведомления',
    unavailable: 'Push-уведомления пока не настроены на сервере',
    error: 'Не удалось проверить состояние уведомлений',
  }
  return labels[state.value] || labels.error
})

function urlBase64ToUint8Array(value) {
  const padding = '='.repeat((4 - (value.length % 4)) % 4)
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = window.atob(base64)
  return Uint8Array.from([...raw].map((character) => character.charCodeAt(0)))
}

async function refreshState() {
  error.value = ''
  if (!supportsPushNotifications()) {
    state.value = 'unsupported'
    return
  }
  if (Notification.permission === 'denied') {
    state.value = 'blocked'
    return
  }

  state.value = 'loading'
  try {
    const [{ data }, serviceWorkerRegistration] = await Promise.all([
      getPushConfigRequest(),
      getServiceWorkerRegistration(),
    ])
    if (!data.configured || !data.vapid_public_key) {
      state.value = 'unavailable'
      return
    }

    publicKey.value = data.vapid_public_key
    registration.value = serviceWorkerRegistration
    subscription.value = await serviceWorkerRegistration.pushManager.getSubscription()
    const activeEndpoints = Array.isArray(data.active_endpoints) ? data.active_endpoints : []
    state.value = subscription.value && activeEndpoints.includes(subscription.value.endpoint) ? 'enabled' : 'disabled'
  } catch (requestError) {
    state.value = 'error'
    error.value = requestError?.response?.data?.detail || 'Повторите попытку позже.'
  }
}

async function enableNotifications() {
  state.value = 'enabling'
  error.value = ''
  let newSubscription = null
  try {
    const permission = await Notification.requestPermission()
    if (permission === 'denied') {
      state.value = 'blocked'
      return
    }
    if (permission !== 'granted') {
      state.value = 'disabled'
      return
    }

    registration.value ||= await getServiceWorkerRegistration()
    const staleSubscription = await registration.value.pushManager.getSubscription()
    if (staleSubscription) await staleSubscription.unsubscribe()
    newSubscription = await registration.value.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey.value),
    })
    await createPushSubscriptionRequest(newSubscription.toJSON())
    subscription.value = newSubscription
    state.value = 'enabled'
  } catch (requestError) {
    if (newSubscription && newSubscription !== subscription.value) {
      await newSubscription.unsubscribe().catch(() => {})
    }
    state.value = 'error'
    error.value = requestError?.response?.data?.detail || 'Не удалось включить уведомления.'
  }
}

async function disableNotifications() {
  state.value = 'disabling'
  error.value = ''
  try {
    subscription.value ||= await registration.value?.pushManager.getSubscription()
    if (subscription.value) {
      await deletePushSubscriptionRequest(subscription.value.endpoint)
      await subscription.value.unsubscribe()
    }
    subscription.value = null
    state.value = 'disabled'
  } catch (requestError) {
    state.value = 'enabled'
    error.value = requestError?.response?.data?.detail || 'Не удалось отключить уведомления.'
  }
}

onMounted(refreshState)
</script>

<template>
  <section class="surface flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div class="flex items-start gap-3">
      <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
        <Bell v-if="enabled" :size="20" />
        <BellOff v-else :size="20" />
      </span>
      <div>
        <h2 class="text-base font-semibold text-slate-950">Уведомления о новых заявках</h2>
        <p class="mt-1 text-sm text-slate-600">{{ statusText }}</p>
        <p v-if="error" class="mt-1 text-sm text-rose-700">{{ error }}</p>
        <p v-if="state === 'blocked'" class="mt-1 text-xs text-slate-500">
          Разрешите уведомления для TrackNode в настройках сайта браузера.
        </p>
      </div>
    </div>
    <button
      v-if="canRetry"
      type="button"
      class="action-button-secondary shrink-0"
      :disabled="busy"
      @click="refreshState"
    >
      Повторить
    </button>
    <button
      v-else-if="canEnable"
      type="button"
      class="action-button-primary shrink-0"
      :disabled="busy"
      @click="enableNotifications"
    >
      <LoaderCircle v-if="state === 'enabling'" :size="17" class="animate-spin" />
      <Bell v-else :size="17" />
      Включить уведомления
    </button>
    <button
      v-else-if="canDisable"
      type="button"
      class="action-button-secondary shrink-0"
      :disabled="busy"
      @click="disableNotifications"
    >
      <BellOff :size="17" />
      Отключить
    </button>
  </section>
</template>
