<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Globe2, Sparkles } from '@lucide/vue'

const route = useRoute()

const isCreateSite = computed(() => route.name === 'onboarding-create-site')
const title = computed(() => (
  isCreateSite.value
    ? 'Создание сайта скоро будет доступно'
    : 'Подключение сайта скоро будет доступно'
))
const description = computed(() => (
  isCreateSite.value
    ? 'Мы готовим мастер создания сайта с помощью AI и готовых профессиональных секций.'
    : 'Здесь пользователь сможет указать адрес сайта и получить персональный скрипт TrackNode.'
))
const icon = computed(() => (isCreateSite.value ? Sparkles : Globe2))
</script>

<template>
  <div class="page-stack">
    <section class="empty-state mx-auto min-h-[26rem] max-w-2xl border-solid p-6 sm:p-8">
      <span class="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
        <component :is="icon" :size="28" />
      </span>
      <h1 class="mt-2 text-2xl font-bold text-[#17223B]">{{ title }}</h1>
      <p class="max-w-lg text-sm leading-6 text-slate-600 sm:text-base">{{ description }}</p>
      <RouterLink to="/onboarding" class="action-button-secondary mt-4">
        <ArrowLeft :size="17" />
        Вернуться к выбору
      </RouterLink>
    </section>
  </div>
</template>
