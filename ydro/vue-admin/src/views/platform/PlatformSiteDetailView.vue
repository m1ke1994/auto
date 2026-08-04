<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertTriangle, Eye, RefreshCw, Trash2 } from '@lucide/vue'

import PlatformPeriodFilter from '../../components/platform/PlatformPeriodFilter.vue'
import { deletePlatformTemplate, getPlatformSite } from '../../api/platform'

const route = useRoute()
const router = useRouter()
const period = ref({ period: '30d' })
const site = ref(null)
const loading = ref(true)
const deletingTemplate = ref(false)
const error = ref('')
const success = ref('')
const templateConfirmation = ref('')

const templateSource = computed(() => site.value?.template_source || null)
const templateDeleteEnabled = computed(() => {
  return Boolean(templateSource.value && templateConfirmation.value.trim() === templateSource.value.name)
})

const statRows = computed(() => [
  ['Посещения', site.value?.visits],
  ['Посетители', site.value?.unique_visitors],
  ['Просмотры', site.value?.page_views],
  ['Заявки', site.value?.leads],
  ['Конверсия', `${site.value?.conversion ?? 0}%`],
  ['Ошибки', site.value?.errors],
  ['Тариф', site.value?.plan || 'Не выбран'],
  ['Подписка', site.value?.subscription_status],
])

function errorMessage(e, fallback) {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  return fallback
}

async function load() {
  loading.value = true
  try {
    site.value = (await getPlatformSite(route.params.siteId, period.value)).data
    error.value = ''
    success.value = ''
    templateConfirmation.value = ''
  } catch (e) {
    error.value = errorMessage(e, 'Сайт не найден.')
  } finally {
    loading.value = false
  }
}

async function confirmTemplateDelete() {
  if (!templateDeleteEnabled.value || deletingTemplate.value) return
  deletingTemplate.value = true
  error.value = ''
  success.value = ''
  try {
    await deletePlatformTemplate(templateSource.value.id, templateConfirmation.value.trim())
    success.value = templateSource.value.is_technical_source
      ? 'Шаблон и его сайт-источник удалены.'
      : 'Шаблон удален из каталога, сайт-источник сохранен.'
    await router.push('/platform/sites')
  } catch (e) {
    error.value = errorMessage(e, 'Не удалось удалить шаблон.')
  } finally {
    deletingTemplate.value = false
  }
}

watch(() => route.params.siteId, load)
onMounted(load)
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-3xl border-2 border-violet-300 bg-violet-50 p-4">
      <p class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-violet-700">
        <Eye :size="16" />
        Просмотр от имени владельца сайта · только чтение
      </p>
      <h2 class="mt-2 text-xl font-bold text-slate-900">{{ site?.name || 'Сайт' }}</h2>
      <p class="text-sm text-slate-600">
        Сейчас открыты данные сайта {{ site?.domain || '' }}. Авторизация пользователя не изменялась.
      </p>
    </div>

    <div class="flex justify-end rounded-3xl bg-slate-900 p-4">
      <PlatformPeriodFilter v-model="period" @change="load" />
    </div>

    <div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div>
    <div v-if="success" class="rounded-2xl bg-emerald-50 p-4 text-emerald-800">{{ success }}</div>
    <div v-if="loading" class="rounded-3xl bg-white p-12 text-center">
      <RefreshCw class="inline animate-spin" />
    </div>

    <template v-else-if="site">
      <section v-if="templateSource" class="rounded-3xl border-2 border-red-200 bg-red-50 p-5">
        <p class="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-red-700">
          <AlertTriangle :size="16" />
          Источник шаблона
        </p>
        <h3 class="mt-2 text-lg font-semibold text-red-950">{{ templateSource.name }}</h3>
        <p class="mt-1 text-sm text-red-800">
          Template ID {{ templateSource.id }} · клиентских клонов: {{ templateSource.cloned_sites_count }}
          · {{ templateSource.is_technical_source ? 'технический source' : 'публичный source будет сохранен' }}
        </p>
        <div class="mt-4 flex flex-col gap-3 sm:flex-row">
          <input
            v-model="templateConfirmation"
            type="text"
            class="min-h-11 flex-1 rounded-xl border border-red-200 bg-white px-3 text-sm outline-none focus:border-red-400"
            :placeholder="`Введите ${templateSource.name}`"
          />
          <button
            type="button"
            class="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-red-700 px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!templateDeleteEnabled || deletingTemplate || templateSource.cloned_sites_count > 0"
            @click="confirmTemplateDelete"
          >
            <Trash2 :size="16" />
            Удалить шаблон
          </button>
        </div>
      </section>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article v-for="item in statRows" :key="item[0]" class="rounded-2xl bg-white p-4 shadow-soft">
          <p class="text-xs text-slate-500">{{ item[0] }}</p>
          <strong class="mt-2 block text-xl">{{ item[1] }}</strong>
        </article>
      </div>

      <div class="grid gap-4 lg:grid-cols-2">
        <article class="rounded-3xl bg-white p-5 shadow-soft">
          <h3 class="font-semibold">Основное</h3>
          <dl class="mt-4 grid grid-cols-2 gap-3 text-sm">
            <dt class="text-slate-500">Владелец</dt>
            <dd>{{ site.owner }} · {{ site.owner_email }}</dd>
            <dt class="text-slate-500">Статус</dt>
            <dd>{{ site.is_active ? 'Активен' : 'Отключён' }}</dd>
            <dt class="text-slate-500">Подключён</dt>
            <dd>{{ new Date(site.created_at).toLocaleString('ru-RU') }}</dd>
            <dt class="text-slate-500">Ключ трекера</dt>
            <dd>{{ site.tracker_key || 'Нет отдельного разрешения' }}</dd>
          </dl>
        </article>

        <article class="rounded-3xl bg-white p-5 shadow-soft">
          <h3 class="font-semibold">Последние заявки</h3>
          <div v-for="lead in site.latest_leads" :key="lead.id" class="mt-3 flex justify-between text-sm">
            <span>{{ lead.name }} · {{ lead.status }}</span>
            <span class="text-slate-500">{{ new Date(lead.created_at).toLocaleDateString('ru-RU') }}</span>
          </div>
          <p v-if="!site.latest_leads.length" class="mt-4 text-sm text-slate-500">Заявок пока нет.</p>
        </article>

        <article class="rounded-3xl bg-white p-5 shadow-soft">
          <h3 class="font-semibold">История проверок сайта</h3>
          <div v-for="item in site.seo_audits" :key="item.id" class="mt-3 flex justify-between text-sm">
            <span>{{ item.status }}</span>
            <b>{{ item.seo_score }}</b>
          </div>
        </article>

        <article class="rounded-3xl bg-white p-5 shadow-soft">
          <h3 class="font-semibold">История AI-рекомендаций</h3>
          <RouterLink
            v-for="item in site.recommendations"
            :key="item.id"
            :to="`/platform/recommendations/${item.id}`"
            class="mt-3 flex justify-between text-sm text-violet-700"
          >
            <span>{{ item.recommendation_type }}</span>
            <span>{{ item.status }}</span>
          </RouterLink>
        </article>
      </div>
    </template>
  </section>
</template>
