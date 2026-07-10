<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight, RefreshCw, Search } from '@lucide/vue'
import { useRoute, useRouter } from 'vue-router'
import PlatformPeriodFilter from '../../components/platform/PlatformPeriodFilter.vue'
import { getPlatformAudit, getPlatformClients, getPlatformLeads, getPlatformRecommendations, getPlatformSeo, getPlatformSites, getPlatformSubscriptions } from '../../api/platform'
const route = useRoute(), router = useRouter(), loading = ref(true), error = ref(''), response = ref({ results: [], count: 0 }), page = ref(1), search = ref(''), period = ref({ period: '30d' })
const configs = {
  'platform-sites': { title: 'Все сайты', load: getPlatformSites, columns: [['name','Сайт'],['domain','Домен'],['owner','Владелец'],['plan','Тариф'],['subscription_status','Подписка'],['visits','Посещения'],['unique_visitors','Посетители'],['page_views','Просмотры'],['leads','Заявки'],['conversion','Конверсия, %'],['errors','Ошибки']], open: (row) => `/platform/sites/${row.id}` },
  'platform-clients': { title: 'Клиенты', load: getPlatformClients, columns: [['username','Пользователь'],['email','Email'],['company','Компания'],['sites_count','Сайты'],['plan','Тариф'],['subscription_status','Подписка'],['visits','Посещения'],['leads','Заявки'],['date_joined','Регистрация']], open: (row) => `/platform/clients/${row.id}` },
  'platform-leads': { title: 'Заявки всех сайтов', load: getPlatformLeads, columns: [['site','Сайт'],['owner','Владелец'],['created_at','Дата'],['name','Клиент'],['phone','Телефон'],['email','Email'],['source','Источник'],['status','Статус']] },
  'platform-recommendations': { title: 'AI-рекомендации', load: getPlatformRecommendations, columns: [['site','Сайт'],['owner','Владелец'],['created_at','Создано'],['type','Тип'],['priority','Приоритет'],['title','Название'],['status','Статус'],['period_from','Начало'],['period_to','Окончание']], open: (row) => `/platform/recommendations/${row.id}` },
  'platform-seo': { title: 'SEO по всем сайтам', load: getPlatformSeo, columns: [['domain','Домен'],['owner','Владелец'],['status','Статус'],['score','Оценка'],['pages','Страницы'],['problems','Проблемы'],['created_at','Создано'],['finished_at','Завершено']] },
  'platform-subscriptions': { title: 'Тарифы и подписки', load: getPlatformSubscriptions, columns: [['client','Клиент'],['owner','Email'],['plan','Тариф'],['status','Статус'],['is_trial','Пробный период'],['paid_until','Оплачено до'],['auto_renew','Автопродление']] },
  'platform-events': { title: 'Системные события', load: getPlatformAudit, columns: [['created_at','Дата'],['actor','Кто'],['action','Действие'],['site','Сайт'],['object_type','Объект'],['object_id','ID'],['ip_address','IP']] },
}
const config = computed(() => configs[route.name] || configs['platform-sites'])
const pages = computed(() => Math.max(1, Math.ceil((response.value.count || 0) / 25)))
function display(value) { if (value === true) return 'Да'; if (value === false) return 'Нет'; if (!value && value !== 0) return '—'; if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) return new Date(value).toLocaleString('ru-RU'); return value }
async function load() { loading.value = true; try { response.value = (await config.value.load({ ...period.value, page: page.value, search: search.value })).data; error.value = '' } catch (e) { error.value = e.response?.status === 403 ? 'У вашей роли нет разрешения на просмотр этого раздела.' : (e.response?.data?.detail || 'Не удалось загрузить данные.') } finally { loading.value = false } }
function open(row) { if (config.value.open) router.push(config.value.open(row)) }
function changePage(next) { page.value = Math.min(Math.max(next, 1), pages.value); load() }
watch(() => route.name, () => { page.value = 1; search.value = ''; load() })
let searchTimer
function searchChanged() { clearTimeout(searchTimer); searchTimer = setTimeout(() => { page.value = 1; load() }, 350) }
onMounted(load)
</script>
<template><section class="space-y-4"><div class="rounded-3xl bg-slate-900 p-4"><div class="flex flex-wrap items-end justify-between gap-3"><div class="text-white"><h2 class="text-lg font-semibold">{{ config.title }}</h2><p class="text-xs text-slate-400">Найдено записей: {{ response.count || 0 }}</p></div><PlatformPeriodFilter v-model="period" @change="page = 1; load()" /></div><label class="relative mt-4 block max-w-md"><Search class="absolute left-3 top-2.5 text-slate-400" :size="17" /><input v-model="search" class="w-full rounded-xl border-0 bg-white py-2 pl-10 pr-3 text-sm" placeholder="Поиск…" @input="searchChanged" /></label></div>
  <div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div><div v-if="loading" class="rounded-3xl bg-white p-12 text-center text-slate-500"><RefreshCw class="mr-2 inline animate-spin" />Загрузка…</div>
  <div v-else class="overflow-hidden rounded-3xl border border-violet-100 bg-white shadow-soft"><div class="overflow-x-auto"><table class="min-w-full text-left text-sm"><thead class="bg-violet-50 text-xs uppercase text-slate-500"><tr><th v-for="[,label] in config.columns" :key="label" class="whitespace-nowrap px-4 py-3">{{ label }}</th></tr></thead><tbody class="divide-y divide-slate-100"><tr v-for="row in response.results" :key="row.id" class="hover:bg-violet-50/50" :class="config.open && 'cursor-pointer'" @click="open(row)"><td v-for="[key] in config.columns" :key="key" class="max-w-xs truncate whitespace-nowrap px-4 py-3">{{ display(row[key]) }}</td></tr><tr v-if="!response.results?.length"><td :colspan="config.columns.length" class="p-10 text-center text-slate-500">Записей не найдено.</td></tr></tbody></table></div><footer class="flex items-center justify-between border-t border-slate-100 p-3"><button class="icon-button" :disabled="page <= 1" @click="changePage(page - 1)"><ChevronLeft /></button><span class="text-xs text-slate-500">Страница {{ page }} из {{ pages }}</span><button class="icon-button" :disabled="page >= pages" @click="changePage(page + 1)"><ChevronRight /></button></footer></div>
</section></template>

