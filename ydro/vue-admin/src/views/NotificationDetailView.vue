<script setup>
import { computed, watch } from 'vue'
import { ArrowLeft, CalendarDays, LoaderCircle, Megaphone } from '@lucide/vue'
import { useRoute } from 'vue-router'

import { useNewsStore } from '../stores/news'

const route = useRoute()
const newsStore = useNewsStore()
const news = computed(() => newsStore.currentNews)

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

async function loadNews(newsId) {
  try {
    const data = await newsStore.fetchNewsDetail(newsId)
    if (!data.is_read) await newsStore.markRead(newsId)
  } catch {
    // Store exposes a user-facing error state.
  }
}

watch(() => route.params.newsId, loadNews, { immediate: true })
</script>

<template>
  <div class="page-stack">
    <RouterLink to="/dashboard/notifications" class="action-button-secondary w-max">
      <ArrowLeft :size="17" />
      К уведомлениям
    </RouterLink>

    <section v-if="newsStore.detailLoading" class="surface flex min-h-64 items-center justify-center gap-3 text-sm text-slate-600">
      <LoaderCircle :size="22" class="animate-spin text-brand-600" />
      Загружаем новость…
    </section>

    <section v-else-if="newsStore.error || !news" class="empty-state">
      <Megaphone :size="30" class="text-slate-400" />
      <h2>Новость недоступна</h2>
      <p>{{ newsStore.error || 'Попробуйте вернуться к списку уведомлений.' }}</p>
    </section>

    <article
      v-else
      class="surface overflow-hidden p-0"
      :class="news.is_important ? 'border-amber-200' : ''"
    >
      <header class="border-b border-brand-100 p-5 sm:p-7" :class="news.is_important ? 'bg-amber-50/70' : 'bg-brand-50/45'">
        <div class="flex flex-wrap items-center gap-2">
          <span v-if="news.is_important" class="status-badge border-amber-200 bg-amber-50 text-amber-800">Важная новость</span>
          <span class="flex items-center gap-1.5 text-xs text-slate-500"><CalendarDays :size="14" />{{ formatDate(news.published_at) }}</span>
        </div>
        <h1 class="mt-4 text-2xl font-bold leading-tight text-[#17223B] sm:text-3xl">{{ news.title }}</h1>
      </header>
      <div class="whitespace-pre-wrap p-5 text-sm leading-7 text-slate-700 sm:p-7 sm:text-base">{{ news.body }}</div>
    </article>
  </div>
</template>

