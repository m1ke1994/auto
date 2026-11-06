<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, ExternalLink, Globe2, RefreshCw } from '@lucide/vue'

import { useAuthStore } from '../stores/auth'
import { toPublicUrl } from '../config/env'
import { useSectionsStore } from '../stores/sections'
import { useSiteStore } from '../stores/site'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const sectionsStore = useSectionsStore()

function openSite(siteId) {
  siteStore.selectSite(siteId)
  sectionsStore.reset()
  router.push(`/sites/${siteId}/overview`)
}

function publicSiteUrl(domain) {
  return toPublicUrl(domain)
}

function siteStatus(site) {
  if (site.is_active === true) return { label: 'Подключён', className: 'status-success' }
  if (site.is_active === false) return { label: 'Отключён', className: 'status-warning' }
  return { label: 'Статус не указан', className: 'status-neutral' }
}

async function refreshSites() {
  try {
    await siteStore.fetchSites()
  } catch {
    // Ошибка отображается через siteStore.error, а не как отсутствие сайтов.
  }
}

onMounted(async () => {
  if (!authStore.user) {
    try { await authStore.getCurrentUser() } catch { /* Auth guard handles sessions. */ }
  }
  if (!siteStore.loaded && !siteStore.loading) await refreshSites()
})
</script>

<template>
  <div class="page-stack">
    <p
      v-if="route.query.registered === '1'"
      class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
    >
      Аккаунт создан. Добро пожаловать в личный кабинет.
    </p>

    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Ваш рабочий кабинет</p>
        <h1>Мои сайты</h1>
        <p>Выберите сайт — покажем, как идут дела и что можно сделать дальше.</p>
      </div>
      <button
        v-if="siteStore.loaded && siteStore.sites.length"
        type="button"
        class="action-button-secondary"
        :disabled="siteStore.loading"
        @click="refreshSites"
      >
        <RefreshCw :size="16" />
        Обновить список
      </button>
    </header>

    <section v-if="siteStore.loading || (!siteStore.loaded && !siteStore.error)" class="empty-state" role="status">
      <span class="loading-dot" />
      <p>Загружаем ваши сайты...</p>
    </section>

    <section v-else-if="siteStore.error" class="empty-state" role="alert">
      <Globe2 :size="28" />
      <h2>Не удалось получить список сайтов</h2>
      <p>Это ошибка загрузки, а не отсутствие сайтов. Попробуйте ещё раз.</p>
      <button type="button" class="action-button-primary mt-3" @click="refreshSites">
        <RefreshCw :size="17" /> Повторить
      </button>
    </section>

    <section v-else-if="siteStore.loaded && siteStore.sites.length === 0" class="empty-state">
      <Globe2 :size="28" />
      <h2>Здесь появятся ваши сайты</h2>
      <p>Аккаунт готов. Для подключения первого сайта свяжитесь с администратором платформы.</p>
    </section>

    <section v-else aria-label="Ваши подключённые сайты">
      <div class="mb-4">
        <h2 class="text-lg font-semibold text-[#17223B]">Выберите сайт</h2>
        <p class="mt-1 text-sm text-slate-500">
          Внутри — заявки клиентов, посещения и настройки сайта.
        </p>
      </div>
      <div class="grid gap-4 lg:grid-cols-2">
        <article v-for="site in siteStore.sites" :key="site.id" class="site-card flex flex-col gap-4">
          <div class="flex items-start justify-between gap-3">
            <div class="flex min-w-0 items-center gap-3">
              <span class="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
                <Globe2 :size="22" />
              </span>
              <div class="min-w-0">
                <h3 class="truncate text-lg font-semibold text-[#17223B]">{{ site.name }}</h3>
                <p class="mt-1 truncate text-sm text-slate-500">{{ site.domain || 'Адрес сайта пока не указан' }}</p>
              </div>
            </div>
            <span class="status-badge shrink-0" :class="siteStatus(site).className">{{ siteStatus(site).label }}</span>
          </div>
          <p class="text-sm leading-6 text-slate-500">
            Откройте обзор, чтобы проверить заявки, посмотреть посещения или изменить содержимое.
          </p>
          <div class="mt-auto flex flex-wrap items-center gap-3 border-t border-brand-100 pt-4">
            <button type="button" class="action-button-primary" @click="openSite(site.id)">
              Перейти к обзору <ArrowRight :size="17" />
            </button>
            <a
              v-if="site.domain"
              :href="publicSiteUrl(site.domain)"
              target="_blank"
              rel="noopener noreferrer"
              class="action-button-secondary"
              :aria-label="'Посмотреть сайт ' + site.name + ' в новой вкладке'"
            >
              <ExternalLink :size="16" /> Посмотреть сайт
            </a>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
