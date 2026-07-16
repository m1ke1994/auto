<script setup>
import { ArrowRight, Globe2, Sparkles, Zap } from '@lucide/vue'
</script>

<template>
  <div class="page-stack">
    <section class="relative overflow-hidden rounded-2xl border border-brand-100 bg-white/85 px-4 py-8 shadow-soft backdrop-blur sm:px-6 lg:px-8">
      <div class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_18%_8%,rgba(109,93,246,0.15),transparent_24rem),radial-gradient(circle_at_92%_18%,rgba(14,165,233,0.12),transparent_22rem)]" />

      <div class="relative mx-auto max-w-4xl text-center">
        <span class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_18px_42px_rgba(109,93,246,0.28)]">
          <Zap :size="24" fill="currentColor" stroke-width="2.2" />
        </span>
        <p class="eyebrow mt-5">Первый шаг</p>
        <h1 class="mt-3 text-3xl font-bold text-[#17223B] sm:text-4xl">Начнём работу с TrackNode</h1>
        <p class="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
          Выберите подходящий вариант, чтобы настроить ваш сайт и подключить возможности платформы.
        </p>
      </div>

      <div class="relative mt-8 grid gap-4 lg:grid-cols-2">
        <article class="site-card flex min-h-[19rem] flex-col p-5 sm:p-6">
          <span class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">
            <Sparkles :size="24" />
          </span>
          <div class="mt-5 flex-1">
            <h2 class="text-xl font-semibold text-[#17223B]">У меня нет сайта</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">
              Создайте новый сайт с нуля. TrackNode поможет подготовить структуру, содержание и подключить все инструменты платформы.
            </p>
          </div>
          <RouterLink to="/onboarding/create-site" class="action-button-primary mt-6 w-full">
            Создать новый сайт
            <ArrowRight :size="17" />
          </RouterLink>
        </article>

        <article class="site-card flex min-h-[19rem] flex-col p-5 sm:p-6">
          <span class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-50 text-sky-700">
            <Globe2 :size="24" />
          </span>
          <div class="mt-5 flex-1">
            <h2 class="text-xl font-semibold text-[#17223B]">У меня есть действующий сайт</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">
              Подключите существующий сайт к TrackNode, чтобы получать аналитику, заявки, SEO-рекомендации и уведомления.
            </p>
          </div>
          <RouterLink to="/onboarding/connect-site" class="action-button-primary mt-6 w-full">
            Подключить действующий сайт
            <ArrowRight :size="17" />
          </RouterLink>
        </article>
      </div>
    </section>
  </div>
</template>
