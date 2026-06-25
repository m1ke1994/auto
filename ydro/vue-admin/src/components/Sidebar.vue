<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  BarChart3,
  Blocks,
  CircleGauge,
  FileSearch,
  Inbox,
  LayoutDashboard,
  SearchCheck,
  Send,
  X,
  Zap,
} from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])
const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()

const siteId = computed(() => siteStore.currentSiteId)
const siteLabel = computed(() => siteStore.currentSite?.name || 'Сайт не выбран')
const userLabel = computed(() => authStore.user?.first_name || authStore.user?.username || 'Пользователь')

const navItems = computed(() => {
  const items = [{ label: 'Мои сайты', to: '/dashboard', icon: LayoutDashboard }]
  if (!siteId.value) return items

  return [
    ...items,
    { label: 'Главная', to: `/sites/${siteId.value}/overview`, icon: CircleGauge },
    { label: 'Заявки', to: `/sites/${siteId.value}/leads`, icon: Inbox },
    { label: 'Аналитика', to: `/sites/${siteId.value}/analytics`, icon: BarChart3 },
    { label: 'Редактирование сайта', to: `/sites/${siteId.value}/sections`, icon: Blocks },
    { label: 'SEO-аудит', to: `/sites/${siteId.value}/seo`, icon: SearchCheck },
    { label: 'Анализ конкурентов', to: `/sites/${siteId.value}/competitors`, icon: FileSearch },
    { label: 'Telegram', to: `/sites/${siteId.value}/integration`, icon: Send },
  ]
})

function isActive(item) {
  if (item.to === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(item.to)
}
</script>

<template>
  <div>
    <button
      v-if="open"
      type="button"
      class="fixed inset-0 z-30 bg-slate-950/25 backdrop-blur-sm lg:hidden"
      aria-label="Закрыть меню"
      @click="emit('close')"
    />

    <aside
      class="fixed inset-y-0 left-0 z-40 flex w-[min(19rem,88vw)] flex-col border-r border-brand-100 bg-white/88 px-4 py-5 text-slate-700 shadow-[0_10px_35px_rgba(32,40,70,0.08)] backdrop-blur-xl transition-transform duration-300 lg:w-64"
      :class="open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
    >
      <div class="flex items-center justify-between gap-3 px-2">
        <div class="flex items-center gap-3">
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_14px_30px_rgba(109,93,246,0.28)]">
            <Zap :size="21" fill="currentColor" stroke-width="2.2" />
          </span>
          <div>
            <p class="text-lg font-semibold text-[#17223B]">TrackNode</p>
            <p class="text-xs text-slate-500">Платформа аналитики</p>
          </div>
        </div>
        <button type="button" class="icon-button lg:hidden" aria-label="Закрыть меню" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <div class="mt-6 rounded-2xl border border-brand-100 bg-brand-50/70 p-3">
        <p class="text-xs text-slate-500">Выбранный сайт</p>
        <p class="mt-1 truncate text-sm font-semibold text-[#17223B]">{{ siteLabel }}</p>
      </div>

      <nav class="mt-5 flex-1 space-y-1 overflow-y-auto">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex min-h-11 items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition duration-300"
          :class="isActive(item) ? 'bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-[0_12px_28px_rgba(109,93,246,0.22)]' : 'text-slate-600 hover:bg-brand-50 hover:text-brand-800'"
          @click="emit('close')"
        >
          <component :is="item.icon" :size="19" class="shrink-0" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="rounded-2xl border border-brand-100 bg-white/72 p-3">
        <p class="truncate text-sm font-semibold text-[#17223B]">{{ userLabel }}</p>
        <p class="mt-1 truncate text-xs text-slate-500">{{ authStore.user?.email || '' }}</p>
      </div>
    </aside>
  </div>
</template>
