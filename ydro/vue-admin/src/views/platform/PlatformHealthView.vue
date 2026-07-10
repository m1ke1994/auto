<script setup>
import { onMounted, ref } from 'vue'
import PlatformPeriodFilter from '../../components/platform/PlatformPeriodFilter.vue'
import { getPlatformHealth } from '../../api/platform'
const period = ref({ period: '30d' }), data = ref(null), error = ref('')
async function load() { try { data.value = (await getPlatformHealth(period.value)).data; error.value = '' } catch (e) { error.value = e.response?.data?.detail || 'Не удалось проверить доступность.' } }
onMounted(load)
</script>
<template><section class="space-y-4"><div class="flex flex-wrap justify-between gap-3 rounded-3xl bg-slate-900 p-4 text-white"><div><h2 class="font-semibold">Ошибки и доступность</h2><p class="text-xs text-slate-400">Состояние событий трекера за период</p></div><PlatformPeriodFilter v-model="period" @change="load" /></div><div v-if="error" class="rounded-2xl bg-red-50 p-4 text-red-800">{{ error }}</div><div v-if="data" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><article v-for="item in [['Состояние API',data.status],['Всего сайтов',data.sites],['Активные сайты',data.active_sites],['Сайты с событиями',data.sites_with_recent_events],['Ошибки',data.errors]]" :key="item[0]" class="rounded-2xl bg-white p-5 shadow-soft"><p class="text-xs text-slate-500">{{ item[0] }}</p><strong class="mt-2 block text-2xl">{{ item[1] }}</strong></article></div></section></template>
