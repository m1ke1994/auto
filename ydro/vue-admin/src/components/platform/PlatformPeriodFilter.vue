<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ modelValue: { type: Object, default: () => ({ period: '30d' }) } })
const emit = defineEmits(['update:modelValue', 'change'])
const value = ref({ period: '30d', ...props.modelValue })
watch(() => props.modelValue, (next) => { value.value = { ...value.value, ...next } }, { deep: true })
function update() { emit('update:modelValue', { ...value.value }); emit('change', { ...value.value }) }
</script>
<template>
  <div class="flex flex-wrap items-end gap-2">
    <label class="text-xs text-violet-200">Период<select v-model="value.period" class="mt-1 block rounded-xl border border-violet-300/30 bg-white px-3 py-2 text-sm text-slate-800" @change="update"><option value="today">Сегодня</option><option value="yesterday">Вчера</option><option value="7d">7 дней</option><option value="30d">30 дней</option><option value="month">Текущий месяц</option><option value="previous_month">Предыдущий месяц</option><option value="custom">Произвольный</option></select></label>
    <template v-if="value.period === 'custom'"><label class="text-xs text-violet-200">С даты<input v-model="value.date_from" type="date" class="mt-1 block rounded-xl border border-violet-300/30 bg-white px-3 py-2 text-sm text-slate-800" @change="update" /></label><label class="text-xs text-violet-200">По дату<input v-model="value.date_to" type="date" class="mt-1 block rounded-xl border border-violet-300/30 bg-white px-3 py-2 text-sm text-slate-800" @change="update" /></label></template>
  </div>
</template>

