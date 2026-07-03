<script setup>
import { computed } from 'vue'

import { useAccessStore } from '../../stores/access'

const accessStore = useAccessStore()

const navItems = computed(() => [
  { label: 'Статистика', to: '/mini', feature: 'dashboard_overview' },
  { label: 'Заявки', to: '/mini/leads', feature: 'leads' },
  { label: 'Проверка сайта', to: '/mini/seo', feature: 'seo_audit' },
  { label: 'Отчёты', to: '/mini/reports', feature: 'reports' },
  { label: 'Настройки', to: '/mini/settings', feature: 'billing_full_access' },
  { label: 'Telegram', to: '/mini/integration', feature: 'telegram' },
].filter((item) => accessStore.can(item.feature)))
</script>

<template>
  <section class="space-y-4">
    <div class="rounded-2xl border border-brand-100 bg-white/92 p-4 shadow-soft">
      <h1 class="text-xl font-semibold text-[#17223B]">Дополнительные инструменты</h1>
      <p class="mt-1 text-sm text-slate-500">Отчёты, настройки и дополнительные возможности сайта.</p>
    </div>

    <div class="rounded-2xl border border-brand-100 bg-white/92 p-2 shadow-soft">
      <nav class="flex flex-wrap gap-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          class="rounded-2xl px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50"
          active-class="bg-brand-50 text-brand-700"
          :to="item.to"
        >{{ item.label }}</RouterLink>
      </nav>
    </div>

    <RouterView />
  </section>
</template>
