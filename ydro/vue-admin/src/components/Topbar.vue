<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, ExternalLink, LogOut, Menu, X } from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useAccessStore } from '../stores/access'
import { toPublicUrl } from '../config/env'
import { useNewsStore } from '../stores/news'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const emit = defineEmits(['toggle-sidebar'])
const router = useRouter()
const authStore = useAuthStore()
const accessStore = useAccessStore()
const newsStore = useNewsStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

const siteTitle = computed(() => siteStore.currentSite?.name || 'Выберите сайт')
const canOpenSite = computed(() => Boolean(siteStore.currentSite?.domain))
const unreadLabel = computed(() => newsStore.unreadCount > 99 ? '99+' : String(newsStore.unreadCount))

function openPublicSite() {
  const domain = siteStore.currentSite?.domain
  if (!domain) return
  window.open(toPublicUrl(domain), '_blank', 'noopener,noreferrer')
}

function logout() {
  accessStore.reset()
  newsStore.reset()
  authStore.logout()
  siteStore.reset()
  sectionsStore.reset()
  router.push('/login')
}

async function openNotifications() {
  try {
    const items = await newsStore.fetchNews()
    if (items.length === 1) {
      await router.push({ name: 'notification-detail', params: { newsId: items[0].id } })
      return
    }
  } catch {
    // The notifications page renders the retry state.
  }
  await router.push({ name: 'notifications' })
}
</script>

<template>
  <header class="dashboard-topbar sticky top-0 z-20 border-b border-brand-100 bg-white/82 shadow-[0_8px_28px_rgba(32,40,70,0.05)] backdrop-blur-xl">
    <div class="dashboard-topbar-inner flex min-h-16 items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-3">
        <button type="button" class="icon-button lg:hidden" aria-label="Открыть меню" @click="emit('toggle-sidebar')">
          <Menu :size="21" />
        </button>
        <div class="min-w-0">
          <p class="text-xs font-medium text-slate-500">Текущий сайт</p>
          <p class="truncate text-base font-semibold text-[#17223B]">{{ siteTitle }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          type="button"
          class="icon-button relative"
          :aria-label="newsStore.unreadCount ? `Уведомления: ${newsStore.unreadCount} непрочитанных` : 'Уведомления'"
          title="Уведомления"
          @click="openNotifications"
        >
          <Bell :size="19" />
          <span
            v-if="newsStore.unreadCount"
            class="absolute -right-1.5 -top-1.5 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold leading-none text-white shadow-sm ring-2 ring-white"
          >{{ unreadLabel }}</span>
        </button>
        <button
          type="button"
          class="action-button-secondary hidden sm:inline-flex"
          :disabled="!canOpenSite"
          @click="openPublicSite"
        >
          <ExternalLink :size="17" />
          Открыть сайт
        </button>
        <button type="button" class="icon-button" aria-label="Выйти" title="Выйти" @click="logout">
          <LogOut :size="19" />
        </button>
      </div>
    </div>

    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-2 opacity-0"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="translate-y-2 opacity-0"
    >
      <div v-if="newsStore.toast" class="fixed left-3 right-3 top-20 z-50 flex items-start gap-3 rounded-2xl border border-brand-200 bg-white/95 p-4 shadow-[0_20px_55px_rgba(32,40,70,0.2)] backdrop-blur-xl sm:left-auto sm:right-5 sm:w-96">
        <button type="button" class="flex min-w-0 flex-1 items-start gap-3 text-left" @click="openNotifications">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700"><Bell :size="19" /></span>
          <span class="min-w-0">
            <strong class="block text-sm text-[#17223B]">{{ newsStore.toast.title }}</strong>
            <span class="mt-1 block text-xs leading-5 text-slate-600">{{ newsStore.toast.body }}</span>
          </span>
        </button>
        <button type="button" class="text-slate-400 hover:text-slate-700" aria-label="Закрыть уведомление" @click="newsStore.dismissToast">
          <X :size="17" />
        </button>
      </div>
    </Transition>
  </header>
</template>
