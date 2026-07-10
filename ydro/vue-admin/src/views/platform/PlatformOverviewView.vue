<script setup>
import { onMounted, ref } from 'vue'
import { AlertTriangle, ArrowRight, RefreshCw } from '@lucide/vue'
import PlatformPeriodFilter from '../../components/platform/PlatformPeriodFilter.vue'
import { getPlatformOverview } from '../../api/platform'
const period = ref({ period: '30d' }), data = ref(null), loading = ref(true), error = ref('')
const labels = { clients_total: 'Всего клиентов', clients_active: 'Активные клиенты', sites_total: 'Всего сайтов', sites_active: 'Активные сайты', sites_without_traffic: 'Без посещений', sites_with_errors: 'С ошибками', visits: 'Посещения', unique_visitors: 'Уникальные посетители', page_views: 'Просмотры страниц', leads_total: 'Все заявки', leads_today: 'Заявки сегодня', leads_period: 'Заявки за период', subscriptions_active: 'Активные подписки', subscriptions_trial: 'Пробный период', subscriptions_expired: 'Просрочены', recommendations: 'AI-рекомендации', critical_recommendations: 'Очень важные рекомендации' }
async function load() { loading.value = true; try { data.value = (await getPlatformOverview(period.value)).data; error.value = '' } catch (e) { error.value = e.response?.data?.detail || 'Не удалось загрузить обзор.' } finally { loading.value = false } }
onMounted(load)
</script>
<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3 rounded-3xl bg-slate-900 p-4"><div class="text-white"><h2 class="font-semibold">Обзор платформы</h2><p class="text-xs text-slate-400">Все показатели рассчитываются на сервере</p></div><PlatformPeriodFilter v-model="period" @change="load" /></div>
    <div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div><div v-if="loading" class="rounded-3xl bg-white p-12 text-center text-slate-500"><RefreshCw class="mr-2 inline animate-spin" />Загрузка…</div>
    <template v-else-if="data"><div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5"><article v-for="(value, key) in data.metrics" :key="key" class="rounded-2xl border border-violet-100 bg-white p-4 shadow-soft"><p class="text-xs text-slate-500">{{ labels[key] || key }}</p><strong class="mt-2 block text-2xl text-slate-900">{{ Number(value).toLocaleString('ru-RU') }}</strong></article></div>
      <div class="rounded-3xl border border-amber-200 bg-white p-5"><h2 class="flex items-center gap-2 font-semibold text-slate-900"><AlertTriangle class="text-amber-500" :size="20" />Требуют внимания</h2><div v-if="!data.attention.length" class="mt-4 text-sm text-slate-500">Сайтов, требующих внимания, сейчас нет.</div><div v-else class="mt-4 grid gap-3 md:grid-cols-2"><RouterLink v-for="item in data.attention" :key="`${item.site_id}-${item.kind}`" :to="`/platform/sites/${item.site_id}`" class="rounded-2xl border border-amber-100 bg-amber-50 p-4"><strong class="text-slate-900">{{ item.site_name }}</strong><p class="mt-1 text-sm text-slate-600">{{ item.reason }}</p><span class="mt-2 flex items-center gap-1 text-xs font-semibold text-violet-700">Открыть сайт <ArrowRight :size="14" /></span></RouterLink></div></div>
    </template>
  </section>
</template>
