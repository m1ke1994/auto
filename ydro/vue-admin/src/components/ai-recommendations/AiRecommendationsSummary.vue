<script setup>
import { AlertCircle, CalendarRange, Gauge, ListChecks } from '@lucide/vue'
defineProps({ items: { type: Array, default: () => [] } })
const icons = { count: ListChecks, high: AlertCircle, date: CalendarRange, period: CalendarRange, potential: Gauge }
</script>
<template><section v-if="items.length" class="grid grid-cols-2 gap-3 lg:grid-cols-5"><article v-for="item in items" :key="item.key" class="rounded-2xl border border-brand-100 bg-white/90 p-4 shadow-soft"><component :is="icons[item.key] || ListChecks" class="text-brand-500" :size="19" /><p class="mt-3 text-xs text-slate-500">{{ item.label }}</p><strong class="mt-1 block break-words text-base text-slate-900 sm:text-lg">{{ item.value }}</strong></article></section></template>

