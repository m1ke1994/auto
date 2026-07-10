<script setup>
import { BrainCircuit, RefreshCw } from '@lucide/vue'
defineProps({ status: { type: String, required: true }, tone: { type: String, default: 'ready' }, busy: Boolean, updatedAt: { type: String, default: '' } })
defineEmits(['refresh'])
</script>
<template>
  <header class="ai-hero relative isolate overflow-hidden rounded-[1.75rem] border border-white/70 bg-gradient-to-br from-white via-brand-50/90 to-violet-100/80 p-5 shadow-[0_22px_60px_rgba(67,56,202,.13)] sm:p-7">
    <div class="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-brand-300/20 blur-3xl" /><div class="pointer-events-none absolute inset-0 opacity-[.22] [background-image:linear-gradient(rgba(99,102,241,.18)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,.18)_1px,transparent_1px)] [background-size:32px_32px]" />
    <div class="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between"><div class="flex min-w-0 gap-4"><span class="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-[0_12px_28px_rgba(79,70,229,.28)]"><BrainCircuit :size="25" /></span><div><p class="text-xs font-bold uppercase tracking-[.16em] text-brand-600">Интеллектуальный помощник</p><h1 class="mt-1 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">AI-рекомендации</h1><p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">Персональные рекомендации для роста сайта на основе данных аналитики, поведения посетителей и эффективности конверсий</p><div class="mt-3 flex flex-wrap items-center gap-2"><span class="h-2.5 w-2.5 rounded-full" :class="{ 'bg-emerald-500': tone === 'ready', 'bg-brand-500 animate-pulse': tone === 'loading', 'bg-amber-500': tone === 'empty', 'bg-red-500': tone === 'error', 'bg-slate-400': tone === 'locked' }" /><strong class="text-sm text-slate-800">{{ status }}</strong><span v-if="updatedAt" class="text-xs text-slate-500">Обновлено {{ updatedAt }}</span></div></div></div><button type="button" class="btn-primary w-full shrink-0 sm:w-auto" :disabled="busy" @click="$emit('refresh')"><RefreshCw :size="17" :class="busy && 'animate-spin'" />{{ busy ? 'Анализируем…' : 'Обновить рекомендации' }}</button></div>
  </header>
</template>

