<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, BarChart3, Blocks, Eraser, ExternalLink, Inbox, SearchCheck, Send, Trash2, X } from '@lucide/vue'

import { getSiteAnalyticsSummaryRequest } from '../api/analytics'
import { getSiteTelegramRequest } from '../api/site'
import DashboardStats from '../components/DashboardStats.vue'
import { toPublicUrl } from '../config/env'
import { useAccessStore } from '../stores/access'
import { useSiteStore } from '../stores/site'

const route = useRoute()
const router = useRouter()
const accessStore = useAccessStore()
const siteStore = useSiteStore()
const loading = ref(false)
const error = ref('')
const success = ref('')
const summary = ref(null)
const telegram = ref(null)
const clearModalOpen = ref(false)
const deleteModalOpen = ref(false)
const clearConfirmation = ref('')
const deleteConfirmation = ref('')
const clearing = ref(false)
const deleting = ref(false)

const siteId = computed(() => Number(route.params.siteId))
const capabilities = computed(() => siteStore.currentSite?.capabilities || {})
const canClearAnalytics = computed(() => Boolean(capabilities.value.clear_analytics))
const canDeleteSite = computed(() => Boolean(capabilities.value.delete))
const ownerLabel = computed(() => {
  const site = siteStore.currentSite
  if (!site?.owner_id) return ''
  return site.owner_email || site.owner_name ? `${site.owner_name || site.owner_email} · ID ${site.owner_id}` : `ID ${site.owner_id}`
})
const stats = computed(() => {
  if (!accessStore.can('analytics')) {
    return [
      { label: 'Разделы сайта', value: siteStore.currentSite?.sections_count ?? 0, sub: 'доступно для редактирования' },
      { label: 'Состояние', value: siteStore.currentSite?.is_active ? 'Работает' : 'Отключён', sub: 'текущий статус сайта' },
    ]
  }
  return [
    { label: 'Заявки', value: summary.value?.leads_count ?? 0, sub: 'за последние 14 дней' },
    { label: 'Посетители', value: summary.value?.visitors_unique ?? 0, sub: 'уникальные пользователи' },
    { label: 'Просмотры', value: summary.value?.pageviews_count ?? 0, sub: 'просмотры страниц' },
    { label: 'Конверсия', value: `${summary.value?.conversion ?? 0}%`, sub: 'посетители, оставившие заявку' },
  ]
})

const actions = computed(() => [
  { label: 'Посмотреть заявки', text: 'Новые обращения клиентов', icon: Inbox, to: `/sites/${siteId.value}/leads`, feature: 'leads' },
  { label: 'Изменить сайт', text: 'Тексты, изображения и разделы', icon: Blocks, to: `/sites/${siteId.value}/sections`, feature: 'site_edit' },
  { label: 'Открыть аналитику', text: 'Посетители и популярные страницы', icon: BarChart3, to: `/sites/${siteId.value}/analytics`, feature: 'analytics' },
  { label: 'Проверить SEO', text: 'Найти проблемы сайта', icon: SearchCheck, to: `/sites/${siteId.value}/seo`, feature: 'seo_audit' },
  { label: telegram.value?.connected ? 'Telegram подключен' : 'Подключить Telegram', text: 'Получать заявки сразу в чат', icon: Send, to: `/sites/${siteId.value}/integration`, feature: 'telegram' },
].filter((action) => accessStore.can(action.feature)))

const clearConfirmationValid = computed(() => {
  const value = clearConfirmation.value.trim()
  return value === 'ОЧИСТИТЬ' || value === siteStore.currentSite?.name
})
const deleteConfirmationValid = computed(() => deleteConfirmation.value.trim() === siteStore.currentSite?.name)
const deleteDataList = [
  'разделы и настройки конструктора',
  'заявки выбранного сайта',
  'аналитика, события, визиты и просмотры',
  'SEO-аудиты, отчёты анализа конкурентов и AI-рекомендации',
  'медиафайлы, привязанные только к этому сайту',
  'ключ трекера и Telegram-настройки сайта',
]

function openPublicSite() {
  const domain = siteStore.currentSite?.domain
  if (!domain) return
  window.open(toPublicUrl(domain), '_blank', 'noopener,noreferrer')
}

function requestErrorMessage(requestError, fallback) {
  const status = requestError?.response?.status
  const detail = requestError?.response?.data?.detail
  const code = requestError?.response?.data?.code
  if (typeof detail === 'string' && detail) return detail
  if (code === 'protected_site') return 'Этот системный сайт нельзя удалить через обычный раздел.'
  if (code === 'protected_template_source') return 'Источник шаблона управляется через каталог шаблонов.'
  if (code === 'site_has_dependencies') return 'Сайт связан с другими объектами и пока не может быть удален.'
  if (code === 'site_has_active_jobs') return 'Сейчас для сайта выполняется фоновая задача. Повторите позже.'
  if (code === 'template_has_cloned_sites') return 'Шаблон используется клиентскими сайтами и не может быть удален.'
  if (status === 400 || code === 'invalid_confirmation') return 'Введите точное подтверждение и повторите действие.'
  if (status === 401) return 'Сессия истекла. Войдите заново.'
  if (status === 403) return 'Недостаточно прав для выполнения действия.'
  if (status === 404) return 'Сайт не найден или уже удалён.'
  if (status === 409) return 'Сейчас для сайта выполняется фоновая задача. Повторите позже.'
  if (status >= 500) return 'На сервере произошла ошибка. Данные не были изменены частично.'
  return fallback
}

function openClearModal() {
  clearConfirmation.value = ''
  clearModalOpen.value = true
  success.value = ''
  error.value = ''
}

function openDeleteModal() {
  deleteConfirmation.value = ''
  deleteModalOpen.value = true
  success.value = ''
  error.value = ''
}

async function confirmClearAnalytics() {
  if (!clearConfirmationValid.value || clearing.value) return
  clearing.value = true
  error.value = ''
  success.value = ''
  try {
    const result = await siteStore.clearSiteAnalytics(siteId.value, clearConfirmation.value.trim())
    clearModalOpen.value = false
    clearConfirmation.value = ''
    success.value = `Аналитика очищена. Удалено записей: ${result.deleted_total ?? 0}.`
    if (accessStore.can('analytics')) {
      const { data } = await getSiteAnalyticsSummaryRequest(siteId.value, { days: 14 })
      summary.value = data
    }
  } catch (e) {
    error.value = requestErrorMessage(e, 'Не удалось очистить аналитику сайта.')
  } finally {
    clearing.value = false
  }
}

async function confirmDeleteSite() {
  if (!deleteConfirmationValid.value || deleting.value) return
  deleting.value = true
  error.value = ''
  success.value = ''
  const deletedSiteId = siteId.value
  try {
    await siteStore.deleteSite(deletedSiteId, deleteConfirmation.value.trim())
    deleteModalOpen.value = false
    deleteConfirmation.value = ''
    const nextSiteId = siteStore.currentSiteId
    if (nextSiteId) {
      router.push(`/sites/${nextSiteId}/overview`)
    } else {
      router.push('/dashboard')
    }
  } catch (e) {
    error.value = requestErrorMessage(e, 'Не удалось удалить сайт.')
  } finally {
    deleting.value = false
  }
}

async function load() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    const requests = []
    if (accessStore.can('analytics')) {
      requests.push(getSiteAnalyticsSummaryRequest(siteId.value, { days: 14 }).then(({ data }) => { summary.value = data }))
    }
    if (accessStore.can('telegram')) {
      requests.push(getSiteTelegramRequest(siteId.value).then(({ data }) => { telegram.value = data }))
    }
    await Promise.all(requests)
  } catch (e) {
    if (e?.response?.data?.code === 'protected_template_source') {
      await router.replace(e.response.data.platform_url || '/platform/sites')
      return
    }
    if (e?.response?.status === 404) {
      await router.replace('/dashboard')
      return
    }
    error.value = e?.response?.data?.detail || 'Не удалось загрузить данные сайта.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Главная</p>
        <h1>{{ siteStore.currentSite?.name || 'Ваш сайт' }}</h1>
        <p>{{ siteStore.currentSite?.domain || 'Домен пока не указан' }}</p>
        <p v-if="ownerLabel" class="mt-1 text-xs text-slate-500">Владелец: {{ ownerLabel }}</p>
      </div>
      <button type="button" class="action-button-secondary" :disabled="!siteStore.currentSite?.domain" @click="openPublicSite">
        <ExternalLink :size="17" />
        Открыть сайт
      </button>
    </header>

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>
    <section v-if="loading" class="empty-state"><span class="loading-dot" /><p>Собираем информацию...</p></section>

    <template v-else>
      <DashboardStats :items="stats" />
      <section>
        <div class="section-heading">
          <div>
            <h2>Быстрые действия</h2>
            <p>Основные задачи всегда под рукой.</p>
          </div>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <button v-for="action in actions" :key="action.to" type="button" class="quick-action" @click="router.push(action.to)">
            <component :is="action.icon" :size="21" />
            <span>
              <strong>{{ action.label }}</strong>
              <small>{{ action.text }}</small>
            </span>
          </button>
        </div>
        <p v-if="!actions.length" class="notice-info mt-3">
          Подключите тариф, чтобы открыть управление сайтом и дополнительные инструменты.
        </p>
      </section>

      <section v-if="canClearAnalytics || canDeleteSite" class="surface border-rose-200 bg-rose-50/40">
        <div class="section-heading">
          <div>
            <h2 class="flex items-center gap-2 text-rose-900">
              <AlertTriangle :size="21" class="text-rose-600" />
              Опасная зона
            </h2>
            <p>Действия ниже необратимы и применяются только к текущему сайту.</p>
          </div>
        </div>
        <div class="flex flex-col gap-3 sm:flex-row">
          <button v-if="canClearAnalytics" type="button" class="action-button-danger" :disabled="clearing || deleting" @click="openClearModal">
            <Eraser :size="18" />
            Очистить аналитику
          </button>
          <button v-if="canDeleteSite" type="button" class="action-button-danger bg-rose-600 text-white hover:bg-rose-700" :disabled="clearing || deleting" @click="openDeleteModal">
            <Trash2 :size="18" />
            Удалить сайт
          </button>
        </div>
      </section>
    </template>

    <div v-if="clearModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <section class="w-full max-w-xl rounded-2xl bg-white p-5 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900">
              <Eraser :size="21" class="text-rose-600" />
              Очистить аналитику
            </h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Все аналитические данные выбранного сайта будут безвозвратно удалены. Сам сайт, его страницы, настройки, заявки и контент останутся без изменений.
            </p>
          </div>
          <button type="button" class="icon-button" :disabled="clearing" aria-label="Закрыть" @click="clearModalOpen = false">
            <X :size="18" />
          </button>
        </div>

        <label class="mt-5 block text-sm font-medium text-slate-700">
          Введите название сайта или ОЧИСТИТЬ
          <input v-model="clearConfirmation" class="form-control mt-2" autocomplete="off">
        </label>

        <div class="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" class="action-button-secondary" :disabled="clearing" @click="clearModalOpen = false">Отмена</button>
          <button type="button" class="action-button-danger" :disabled="!clearConfirmationValid || clearing" @click="confirmClearAnalytics">
            <span v-if="clearing" class="button-spinner" aria-hidden="true" />
            <Eraser v-else :size="18" />
            {{ clearing ? 'Очищаем...' : 'Очистить аналитику' }}
          </button>
        </div>
      </section>
    </div>

    <div v-if="deleteModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <section class="w-full max-w-2xl rounded-2xl bg-white p-5 shadow-2xl">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="flex items-center gap-2 text-lg font-bold text-slate-900">
              <Trash2 :size="21" class="text-rose-600" />
              Удалить сайт
            </h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Сайт и связанные с ним данные будут безвозвратно удалены. Это действие нельзя отменить.
            </p>
          </div>
          <button type="button" class="icon-button" :disabled="deleting" aria-label="Закрыть" @click="deleteModalOpen = false">
            <X :size="18" />
          </button>
        </div>

        <dl class="mt-5 grid gap-3 rounded-2xl border border-rose-100 bg-rose-50/50 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt class="font-medium text-slate-500">Название</dt>
            <dd class="mt-1 text-slate-900">{{ siteStore.currentSite?.name || 'Сайт' }}</dd>
          </div>
          <div>
            <dt class="font-medium text-slate-500">Домен</dt>
            <dd class="mt-1 text-slate-900">{{ siteStore.currentSite?.domain || 'Не указан' }}</dd>
          </div>
          <div>
            <dt class="font-medium text-slate-500">Создан</dt>
            <dd class="mt-1 text-slate-900">{{ siteStore.currentSite?.created_at ? new Date(siteStore.currentSite.created_at).toLocaleString('ru-RU') : 'Неизвестно' }}</dd>
          </div>
        </dl>

        <div class="mt-5">
          <h3 class="text-sm font-semibold text-slate-900">Будет удалено</h3>
          <ul class="mt-2 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
            <li v-for="item in deleteDataList" :key="item" class="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">{{ item }}</li>
          </ul>
        </div>

        <label class="mt-5 block text-sm font-medium text-slate-700">
          Введите точное название сайта
          <input v-model="deleteConfirmation" class="form-control mt-2" autocomplete="off">
        </label>

        <div class="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" class="action-button-secondary" :disabled="deleting" @click="deleteModalOpen = false">Отмена</button>
          <button type="button" class="action-button-danger bg-rose-600 text-white hover:bg-rose-700" :disabled="!deleteConfirmationValid || deleting" @click="confirmDeleteSite">
            <span v-if="deleting" class="button-spinner" aria-hidden="true" />
            <Trash2 v-else :size="18" />
            {{ deleting ? 'Удаляем...' : 'Удалить сайт' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
