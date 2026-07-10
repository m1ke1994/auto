<script setup>
import { Activity, BarChart3, Bot, Building2, CircleDollarSign, FileSearch, HeartPulse, LayoutDashboard, ListChecks, MessageSquareText, Users } from '@lucide/vue'
const links = [
  { to: '/platform', label: 'Обзор платформы', icon: LayoutDashboard }, { to: '/platform/sites', label: 'Все сайты', icon: Building2 },
  { to: '/platform/analytics', label: 'Общая аналитика', icon: BarChart3 }, { to: '/platform/clients', label: 'Клиенты', icon: Users },
  { to: '/platform/leads', label: 'Заявки', icon: MessageSquareText }, { to: '/platform/seo', label: 'SEO', icon: FileSearch },
  { to: '/platform/recommendations', label: 'AI-рекомендации', icon: Bot }, { to: '/platform/subscriptions', label: 'Тарифы и подписки', icon: CircleDollarSign },
  { to: '/platform/health', label: 'Ошибки и доступность', icon: HeartPulse }, { to: '/platform/events', label: 'Системные события', icon: ListChecks },
]
</script>
<template>
  <div class="space-y-5">
    <header class="overflow-hidden rounded-3xl bg-gradient-to-r from-slate-950 via-violet-950 to-indigo-900 p-5 text-white shadow-xl">
      <div class="flex flex-wrap items-center justify-between gap-4"><div><p class="flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] text-violet-200"><Activity :size="15" /> Режим владельца TrackNode</p><h1 class="mt-2 text-2xl font-bold">Управление платформой</h1><p class="mt-1 text-sm text-violet-100/80">Глобальные данные всех подключённых сайтов</p></div><RouterLink to="/dashboard" class="rounded-xl border border-white/20 bg-white/10 px-4 py-2 text-sm hover:bg-white/20">Вернуться в кабинет</RouterLink></div>
      <nav class="mt-5 flex gap-2 overflow-x-auto pb-1"><RouterLink v-for="item in links" :key="item.to" :to="item.to" class="flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold text-violet-100 hover:bg-white/10" active-class="bg-white text-violet-900"><component :is="item.icon" :size="15" />{{ item.label }}</RouterLink></nav>
    </header>
    <RouterView />
  </div>
</template>

