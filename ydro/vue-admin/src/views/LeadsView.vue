<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Inbox, RefreshCw, Trash2, X } from '@lucide/vue'

import { useLeadsStore } from '../stores/leads'
import { useSiteStore } from '../stores/site'
import PushNotificationsCard from '../components/PushNotificationsCard.vue'

const route = useRoute()
const siteStore = useSiteStore()
const leadsStore = useLeadsStore()
const error = ref('')
const success = ref('')
const updatingLeadId = ref(null)
const deletingLeadId = ref(null)
const selectedLead = ref(null)
const statusFilter = ref('')

const siteId = computed(() => Number(route.params.siteId))
const leads = computed(() => leadsStore.leads)
const statusOptions = [
  { value: 'new', label: 'Новая', class: 'status-danger' },
  { value: 'in_progress', label: 'В работе', class: 'status-warning' },
  { value: 'done', label: 'Завершена', class: 'status-success' },
  { value: 'archived', label: 'Спам', class: 'status-neutral' },
]

function statusOption(value) {
  return statusOptions.find((item) => item.value === value) || statusOptions[0]
}

function formatDate(value) {
  if (!value) return 'Не указано'
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function pageLabel(value) {
  if (!value) return 'Не указано'
  try {
    const url = new URL(value)
    return url.pathname || '/'
  } catch {
    return value
  }
}

async function load() {
  error.value = ''
  success.value = ''
  try {
    siteStore.selectSite(siteId.value)
    if (!siteStore.currentSite) await siteStore.fetchSite(siteId.value)
    await leadsStore.fetchLeads({ siteId: siteId.value, status: statusFilter.value })
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось загрузить заявки. Попробуйте обновить страницу.'
  }
}

async function updateStatus(lead, status) {
  if (!status || status === lead.status) return
  updatingLeadId.value = lead.id
  error.value = ''
  success.value = ''
  try {
    const updated = await leadsStore.patchLeadStatus(lead.id, status)
    if (selectedLead.value?.id === lead.id) selectedLead.value = updated
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось изменить статус заявки.'
  } finally {
    updatingLeadId.value = null
  }
}

async function deleteLead(lead) {
  if (!lead?.id) return
  const leadTitle = lead.name || lead.phone || `#${lead.id}`
  if (!window.confirm(`Удалить заявку ${leadTitle}? Это действие нельзя отменить.`)) return
  deletingLeadId.value = lead.id
  error.value = ''
  success.value = ''
  try {
    await leadsStore.deleteLead(lead.id)
    if (selectedLead.value?.id === lead.id) selectedLead.value = null
    success.value = 'Заявка удалена.'
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось удалить заявку.'
  } finally {
    deletingLeadId.value = null
  }
}

async function openLead(leadId) {
  try {
    selectedLead.value = await leadsStore.fetchLead(leadId)
  } catch (e) {
    error.value = e?.response?.data?.detail || 'Не удалось открыть заявку.'
  }
}

onMounted(async () => {
  await load()
  const leadId = Number(route.query.lead)
  if (Number.isInteger(leadId) && leadId > 0) await openLead(leadId)
})
</script>

<template>
  <div class="page-stack">
    <header class="page-heading page-heading-actions">
      <div>
        <p class="eyebrow">Обращения клиентов</p>
        <h1>Заявки</h1>
        <p>Все обращения с сайта {{ siteStore.currentSite?.name || '' }} в одном месте.</p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <select v-model="statusFilter" class="form-control sm:w-44" @change="load">
          <option value="">Все статусы</option>
          <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
        </select>
        <button type="button" class="action-button-secondary" @click="load">
          <RefreshCw :size="17" />
          Обновить
        </button>
      </div>
    </header>

    <PushNotificationsCard />

    <p v-if="error" class="notice-error">{{ error }}</p>
    <p v-if="success" class="notice-success">{{ success }}</p>
    <section v-if="leadsStore.loading" class="empty-state"><span class="loading-dot" /><p>Загружаем заявки...</p></section>
    <section v-else-if="leads.length === 0" class="empty-state">
      <Inbox :size="30" />
      <h2>Заявок пока нет</h2>
      <p>Когда посетитель заполнит форму на сайте, его обращение появится здесь.</p>
    </section>

    <template v-else>
      <section class="surface hidden overflow-x-auto lg:block">
        <table class="data-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Клиент</th>
              <th>Контакты</th>
              <th>Комментарий</th>
              <th>Страница</th>
              <th>Статус</th>
              <th><span class="sr-only">Действия</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id">
              <td class="whitespace-nowrap">{{ formatDate(lead.created_at) }}</td>
              <td class="font-semibold text-slate-950">{{ lead.name || 'Имя не указано' }}</td>
              <td>
                <a v-if="lead.phone" :href="`tel:${lead.phone}`" class="block font-medium text-brand-800">{{ lead.phone }}</a>
                <a v-if="lead.email" :href="`mailto:${lead.email}`" class="mt-1 block text-xs text-slate-500">{{ lead.email }}</a>
              </td>
              <td class="max-w-64"><p class="line-clamp-2">{{ lead.message || 'Без комментария' }}</p></td>
              <td>{{ pageLabel(lead.source_url) }}</td>
              <td>
                <select :value="lead.status" class="form-control min-w-36" :disabled="updatingLeadId === lead.id" @change="updateStatus(lead, $event.target.value)">
                  <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </td>
              <td>
                <div class="flex items-center justify-end gap-2">
                  <button type="button" class="action-button-secondary min-h-9 px-3 py-1.5" @click="openLead(lead.id)">Подробнее</button>
                  <button
                    type="button"
                    class="action-button-danger min-h-9 px-3 py-1.5"
                    :disabled="deletingLeadId === lead.id"
                    @click="deleteLead(lead)"
                  >
                    <Trash2 :size="16" />
                    Удалить
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="grid gap-3 lg:hidden">
        <article v-for="lead in leads" :key="lead.id" class="surface">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate font-semibold text-slate-950">{{ lead.name || 'Имя не указано' }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ formatDate(lead.created_at) }}</p>
            </div>
            <span class="status-badge" :class="statusOption(lead.status).class">{{ statusOption(lead.status).label }}</span>
          </div>
          <div class="mt-4 grid gap-2 text-sm text-slate-600">
            <a v-if="lead.phone" :href="`tel:${lead.phone}`" class="font-medium text-brand-800">{{ lead.phone }}</a>
            <a v-if="lead.email" :href="`mailto:${lead.email}`">{{ lead.email }}</a>
            <p>{{ lead.message || 'Без комментария' }}</p>
            <p class="text-xs text-slate-500">Страница: {{ pageLabel(lead.source_url) }}</p>
          </div>
          <div class="mt-4 flex flex-col gap-2 sm:flex-row">
            <select :value="lead.status" class="form-control flex-1" @change="updateStatus(lead, $event.target.value)">
              <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <button type="button" class="action-button-secondary" @click="openLead(lead.id)">Подробнее</button>
            <button type="button" class="action-button-danger" :disabled="deletingLeadId === lead.id" @click="deleteLead(lead)">
              <Trash2 :size="17" />
              Удалить
            </button>
          </div>
        </article>
      </section>
    </template>

    <div
      v-if="selectedLead"
      class="fixed inset-0 z-50 flex items-end bg-slate-950/60 sm:items-center sm:justify-center sm:p-5"
      role="presentation"
      @click.self="selectedLead = null"
    >
      <section
        class="flex max-h-[94vh] max-h-[94dvh] w-full flex-col overflow-hidden rounded-t-[24px] border border-slate-200 bg-white shadow-[0_30px_90px_rgba(15,23,42,0.34)] sm:max-w-2xl sm:rounded-[24px]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lead-dialog-title"
      >
        <header class="flex shrink-0 items-start justify-between gap-4 border-b border-slate-200 bg-white px-5 py-4 sm:px-6 sm:py-5">
          <div class="min-w-0">
            <p class="eyebrow">Карточка заявки</p>
            <h2 id="lead-dialog-title" class="mt-1 break-words text-xl font-semibold text-slate-950 sm:text-2xl">
              {{ selectedLead.name || 'Имя не указано' }}
            </h2>
          </div>
          <button
            type="button"
            class="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-slate-200 bg-slate-100 text-slate-700 transition hover:border-slate-300 hover:bg-slate-200 hover:text-slate-950 focus:outline-none focus:ring-4 focus:ring-indigo-100"
            aria-label="Закрыть карточку заявки"
            @click="selectedLead = null"
          >
            <X :size="20" />
          </button>
        </header>

        <div class="overflow-y-auto bg-white px-5 py-5 sm:px-6 sm:py-6">
          <div class="grid gap-3 sm:grid-cols-2 sm:gap-4">
            <article class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Дата</p>
              <p class="mt-1.5 break-words text-[15px] font-semibold leading-6 text-slate-800">{{ formatDate(selectedLead.created_at) }}</p>
            </article>
            <article class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Статус</p>
              <span class="status-badge mt-2" :class="statusOption(selectedLead.status).class">{{ statusOption(selectedLead.status).label }}</span>
            </article>
            <article class="min-w-0 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Телефон</p>
              <a
                v-if="selectedLead.phone"
                :href="`tel:${selectedLead.phone}`"
                class="mt-1.5 block break-all text-[15px] font-semibold leading-6 text-brand-800 hover:underline"
              >
                {{ selectedLead.phone }}
              </a>
              <p v-else class="mt-1.5 text-[15px] font-semibold leading-6 text-slate-700">Не указан</p>
            </article>
            <article class="min-w-0 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Электронная почта</p>
              <a
                v-if="selectedLead.email"
                :href="`mailto:${selectedLead.email}`"
                class="mt-1.5 block break-all text-[15px] font-semibold leading-6 text-brand-800 hover:underline"
              >
                {{ selectedLead.email }}
              </a>
              <p v-else class="mt-1.5 text-[15px] font-semibold leading-6 text-slate-700">Не указана</p>
            </article>
            <article class="min-w-0 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Форма</p>
              <p class="mt-1.5 break-words text-[15px] font-semibold leading-6 text-slate-800">{{ selectedLead.form_name || 'Не указана' }}</p>
            </article>
            <article class="min-w-0 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Источник</p>
              <p class="mt-1.5 break-all text-[15px] font-semibold leading-6 text-slate-800">{{ pageLabel(selectedLead.source_url) }}</p>
            </article>
            <article class="min-w-0 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5 sm:col-span-2">
              <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Комментарий</p>
              <p class="mt-1.5 whitespace-pre-wrap break-words text-[15px] font-medium leading-7 text-slate-800">{{ selectedLead.message || 'Не указан' }}</p>
            </article>
          </div>
        </div>

        <footer class="flex shrink-0 justify-end border-t border-slate-200 bg-slate-50 px-5 py-4 sm:px-6">
          <button
            type="button"
            class="action-button-danger w-full justify-center shadow-sm sm:w-auto"
            :disabled="deletingLeadId === selectedLead.id"
            @click="deleteLead(selectedLead)"
          >
            <Trash2 :size="17" />
            Удалить заявку
          </button>
        </footer>
      </section>
    </div>
  </div>
</template>
