<script setup>
import { computed } from 'vue'
import { ArrowRight, BarChart3, LayoutDashboard, LockKeyhole } from '@lucide/vue'

import { useAccessStore } from '../stores/access'

const accessStore = useAccessStore()

const description = computed(() => {
  if (accessStore.planCode === 'content_hosting') {
    return 'Текущий тариф включает управление сайтом, заявки и уведомления. Для аналитики, SEO-аудита, анализа конкурентов и расширенных рекомендаций подключите тариф Бизнес-аналитика.'
  }
  return 'Для доступа к аналитике, SEO-аудиту, анализу конкурентов и расширенным рекомендациям выберите тариф Бизнес-аналитика.'
})
</script>

<template>
  <div class="mx-auto grid min-h-[60vh] w-full max-w-3xl place-items-center py-8">
    <section class="surface w-full overflow-hidden p-0 text-center">
      <div class="bg-gradient-to-br from-brand-50 via-white to-violet-50 px-6 py-10 sm:px-10">
        <span class="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white text-brand-700 shadow-[0_16px_38px_rgba(109,93,246,0.18)]">
          <LockKeyhole :size="30" />
        </span>
        <p class="eyebrow mt-6">Ограничение тарифа</p>
        <h1 class="mx-auto mt-4 max-w-2xl text-2xl font-bold leading-tight text-[#17223B] sm:text-3xl">
          Функция доступна на тарифе Бизнес-аналитика
        </h1>
        <p class="mx-auto mt-4 max-w-2xl text-sm leading-7 text-slate-600 sm:text-base">{{ description }}</p>
        <div class="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
          <RouterLink to="/billing" class="action-button-primary">
            <BarChart3 :size="18" />
            Перейти к тарифам
            <ArrowRight :size="17" />
          </RouterLink>
          <RouterLink to="/dashboard" class="action-button-secondary">
            <LayoutDashboard :size="18" />
            Вернуться на главную
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

