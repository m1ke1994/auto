<script setup>
import { computed, onMounted } from 'vue'
import { Bell, BellRing, CalendarDays, ChevronRight, LoaderCircle, Megaphone } from '@lucide/vue'

import { useNewsStore } from '../stores/news'

const newsStore = useNewsStore()
const newsItems = computed(() => newsStore.items)
const canRequestPermission = computed(() => newsStore.browserPermission === 'default')
const permissionBlocked = computed(() => newsStore.browserPermission === 'denied')

function formatDate(value) {
  if (!value) return 'Дата не указана'
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function loadNews() {
  newsStore.fetchNews().catch(() => {})
}

onMounted(loadNews)
</script>

<template>
  <div class="page-stack">
    <div class="page-heading-actions">
      <div class="page-heading">
        <p class="eyebrow">Новости TrackNode</p>
        <h1>Уведомления</h1>
        <p>Обновления платформы, важные сообщения и новые возможности сервиса.</p>
      </div>
      <button v-if="canRequestPermission" type="button" class="action-button-secondary" @click="newsStore.requestBrowserPermission">
        <Bell :size="18" />
        Включить уведомления браузера
      </button>
    </div>

    <p v-if="permissionBlocked" class="notice-info">
      Системные уведомления заблокированы в браузере. Badge и список новостей продолжат работать.
    </p>

    <section v-if="newsStore.loading" class="surface flex min-h-48 items-center justify-center gap-3 text-sm text-slate-600">
      <LoaderCircle :size="22" class="animate-spin text-brand-600" />
      Загружаем новости…
    </section>

    <section v-else-if="newsStore.error" class="empty-state">
      <BellRing :size="30" class="text-rose-500" />
      <h2>Не удалось загрузить уведомления</h2>
      <p>{{ newsStore.error }}</p>
      <button type="button" class="action-button-secondary mt-3" @click="loadNews">Повторить</button>
    </section>

    <section v-else-if="!newsItems.length" class="empty-state">
      <Bell :size="32" class="text-brand-500" />
      <h2>Уведомлений пока нет</h2>
      <p>Здесь появятся новости и важные сообщения от команды TrackNode.</p>
    </section>

    <section v-else class="grid gap-3">
      <RouterLink
        v-for="news in newsItems"
        :key="news.id"
        :to="{ name: 'notification-detail', params: { newsId: news.id } }"
        class="group relative grid gap-4 rounded-2xl border bg-white/90 p-5 text-left shadow-soft transition hover:-translate-y-0.5 hover:shadow-[0_18px_48px_rgba(32,40,70,0.12)] sm:grid-cols-[auto_1fr_auto] sm:items-center"
        :class="news.is_important ? 'border-amber-200 bg-gradient-to-r from-amber-50/80 to-white' : 'border-brand-100'"
      >
        <span
          class="flex h-11 w-11 items-center justify-center rounded-xl"
          :class="news.is_important ? 'bg-amber-100 text-amber-700' : news.is_read ? 'bg-slate-100 text-slate-500' : 'bg-brand-50 text-brand-700'"
        >
          <Megaphone :size="21" />
        </span>
        <span class="min-w-0">
          <span class="flex flex-wrap items-center gap-2">
            <strong class="text-base text-[#17223B]">{{ news.title }}</strong>
            <span v-if="news.is_important" class="status-badge border-amber-200 bg-amber-50 text-amber-800">Важно</span>
            <span v-if="!news.is_read" class="status-badge status-neutral">Новое</span>
          </span>
          <span class="mt-2 block text-sm leading-6 text-slate-600">{{ news.short_body }}</span>
          <span class="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
            <CalendarDays :size="14" />{{ formatDate(news.published_at) }}
          </span>
        </span>
        <ChevronRight :size="20" class="text-slate-400 transition group-hover:translate-x-1 group-hover:text-brand-600" />
      </RouterLink>
    </section>
  </div>
</template>

