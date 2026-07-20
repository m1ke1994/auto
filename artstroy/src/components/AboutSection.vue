<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const statsGridRef = ref(null)
const animatedValues = ref([0, 0, 0, 0])
const counterTargets = [10, 250, 98, 50]

let countersStarted = false
let countersObserver = null
const rafIds = []

const isReducedMotion = () => {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const easeOutCubic = (progress) => 1 - (1 - progress) ** 3

const clearCounterRafs = () => {
  rafIds.forEach((id) => {
    if (id) {
      window.cancelAnimationFrame(id)
    }
  })
  rafIds.length = 0
}

const animateCounter = (index, target, durationMs, delayMs) => {
  let rafId = 0
  let startTime = 0

  const tick = (time) => {
    if (!startTime) startTime = time

    const elapsed = time - startTime - delayMs
    if (elapsed < 0) {
      rafId = window.requestAnimationFrame(tick)
      rafIds[index] = rafId
      return
    }

    const progress = Math.min(elapsed / durationMs, 1)
    const value = Math.round(target * easeOutCubic(progress))
    animatedValues.value[index] = value

    if (progress < 1) {
      rafId = window.requestAnimationFrame(tick)
      rafIds[index] = rafId
      return
    }

    animatedValues.value[index] = target
  }

  rafId = window.requestAnimationFrame(tick)
  rafIds[index] = rafId
}

const startCounters = () => {
  if (countersStarted) return
  countersStarted = true

  if (isReducedMotion()) {
    animatedValues.value = [...counterTargets]
    return
  }

  counterTargets.forEach((target, index) => {
    const durationMs = 1200 + Math.min(target / 250, 1) * 450
    const delayMs = index * 110
    animateCounter(index, target, durationMs, delayMs)
  })
}

onMounted(() => {
  if (typeof window === 'undefined') return

  if (!('IntersectionObserver' in window) || !statsGridRef.value) {
    startCounters()
    return
  }

  countersObserver = new IntersectionObserver(
    (entries) => {
      const visible = entries.some((entry) => entry.isIntersecting)
      if (!visible) return

      startCounters()
      countersObserver?.disconnect()
      countersObserver = null
    },
    {
      threshold: 0.24,
      rootMargin: '0px 0px -10% 0px',
    },
  )

  countersObserver.observe(statsGridRef.value)
})

onBeforeUnmount(() => {
  clearCounterRafs()
  countersObserver?.disconnect()
  countersObserver = null
})
</script>

<template>
  <section id="about" class="w-full scroll-mt-28 bg-transparent text-[#181a21]">
    <div class="w-full px-5 py-10 sm:px-8 sm:py-12 lg:px-12 lg:py-14">
      <div class="flex min-h-[620px] flex-col p-6 sm:p-8 lg:p-10">
        <div>
          <p
            v-reveal="{ type: 'title', delay: 0 }"
            class="text-center text-[0.75rem] font-semibold uppercase tracking-[0.16em] text-[#6b7280]"
          >
            О компании
          </p>

          <h2
            v-reveal="{ type: 'title', delay: 0.08 }"
            class="mx-auto mt-4 max-w-[58rem] text-center text-[2rem] font-semibold leading-[1.05] tracking-[-0.03em] text-[#111827] sm:text-[2.7rem] lg:text-[3.4rem]"
          >
            Инженерия, эстетика, надежность
          </h2>

          <p
            v-reveal="{ type: 'title', delay: 0.16 }"
            class="mx-auto mt-5 max-w-[46rem] text-center text-[1rem] leading-[1.75] text-[#4b5563]"
          >
            Мы объединяем инженерную точность, архитектурную эстетику и надежный подход к реализации, чтобы создавать объекты, которые служат долго, выглядят современно и подчеркивают статус проекта.
          </p>

          <div class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <article
              v-reveal="{ type: 'card-right', delay: 0.05, mobileAlternate: true, mobileIndex: 0 }"
              class="group flex h-full flex-col items-center rounded-[1.25rem] border border-[#5b6169]/35 bg-white/26 p-5 text-center shadow-[0_12px_30px_rgba(16,24,40,0.1)] backdrop-blur-[10px] transition duration-300 hover:-translate-y-[2px] hover:border-[#5b6169]/55 hover:shadow-[0_16px_36px_rgba(16,24,40,0.14)] sm:p-6"
            >
              <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#5b6169]/45 bg-white/60 text-[#374151]">
                <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="m12 4 7 4-7 4-7-4 7-4Z" />
                  <path d="m5 12 7 4 7-4" />
                  <path d="m5 16 7 4 7-4" />
                </svg>
              </div>
              <h3 class="text-[1.35rem] font-semibold leading-[1.15] tracking-[-0.02em] text-[#111827] sm:text-[1.5rem]">
                Комплексный подход
              </h3>
              <p class="mt-3 text-[0.9375rem] leading-[1.7] text-[#4b5563]">
                От проектирования до монтажа под ключ — все этапы в одних руках. Координируем процесс целиком и отвечаем за результат.
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-right', delay: 0.13, mobileAlternate: true, mobileIndex: 1 }"
              class="group flex h-full flex-col items-center rounded-[1.25rem] border border-[#5b6169]/35 bg-white/26 p-5 text-center shadow-[0_12px_30px_rgba(16,24,40,0.1)] backdrop-blur-[10px] transition duration-300 hover:-translate-y-[2px] hover:border-[#5b6169]/55 hover:shadow-[0_16px_36px_rgba(16,24,40,0.14)] sm:p-6"
            >
              <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#5b6169]/45 bg-white/60 text-[#374151]">
                <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M12 3 5 6v6c0 4.5 2.7 7.9 7 9 4.3-1.1 7-4.5 7-9V6l-7-3Z" />
                  <path d="m9.5 12 1.8 1.8 3.5-3.5" />
                </svg>
              </div>
              <h3 class="text-[1.35rem] font-semibold leading-[1.15] tracking-[-0.02em] text-[#111827] sm:text-[1.5rem]">
                Надежные решения
              </h3>
              <p class="mt-3 text-[0.9375rem] leading-[1.7] text-[#4b5563]">
                Используем проверенные материалы, точные инженерные расчеты и технологии, рассчитанные на долговечную эксплуатацию.
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-right', delay: 0.21, mobileAlternate: true, mobileIndex: 2 }"
              class="group flex h-full flex-col items-center rounded-[1.25rem] border border-[#5b6169]/35 bg-white/26 p-5 text-center shadow-[0_12px_30px_rgba(16,24,40,0.1)] backdrop-blur-[10px] transition duration-300 hover:-translate-y-[2px] hover:border-[#5b6169]/55 hover:shadow-[0_16px_36px_rgba(16,24,40,0.14)] sm:p-6"
            >
              <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#5b6169]/45 bg-white/60 text-[#374151]">
                <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M4 6.5h16" />
                  <path d="M8 3.5v6" />
                  <path d="M16 3.5v6" />
                  <rect x="4" y="8" width="16" height="12" rx="2" />
                  <path d="m9 15 2 2 4-4" />
                </svg>
              </div>
              <h3 class="text-[1.35rem] font-semibold leading-[1.15] tracking-[-0.02em] text-[#111827] sm:text-[1.5rem]">
                Современный дизайн
              </h3>
              <p class="mt-3 text-[0.9375rem] leading-[1.7] text-[#4b5563]">
                Продумываем эстетику, пропорции и функциональность, чтобы объект выглядел актуально, выразительно и гармонично.
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-right', delay: 0.29, mobileAlternate: true, mobileIndex: 3 }"
              class="group flex h-full flex-col items-center rounded-[1.25rem] border border-[#5b6169]/35 bg-white/26 p-5 text-center shadow-[0_12px_30px_rgba(16,24,40,0.1)] backdrop-blur-[10px] transition duration-300 hover:-translate-y-[2px] hover:border-[#5b6169]/55 hover:shadow-[0_16px_36px_rgba(16,24,40,0.14)] sm:p-6"
            >
              <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-[#5b6169]/45 bg-white/60 text-[#374151]">
                <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="12" cy="12" r="8" />
                  <path d="M12 8v4l2.5 2.5" />
                </svg>
              </div>
              <h3 class="text-[1.35rem] font-semibold leading-[1.15] tracking-[-0.02em] text-[#111827] sm:text-[1.5rem]">
                Соблюдаем сроки
              </h3>
              <p class="mt-3 text-[0.9375rem] leading-[1.7] text-[#4b5563]">
                Четко планируем этапы, контролируем выполнение работ и держим проект в согласованных временных рамках.
              </p>
            </article>
          </div>
        </div>

        <hr class="my-8 border-0 border-t border-[#5b6169]/45" />

        <div class="mt-auto">
          <div ref="statsGridRef" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <article
              v-reveal="{ type: 'card-left', delay: 0.05, mobileAlternate: true, mobileIndex: 4 }"
              class="rounded-[1rem] border border-[#5b6169]/40 bg-white/22 px-4 py-5 text-center shadow-[0_10px_24px_rgba(16,24,40,0.1)] backdrop-blur-[8px]"
            >
              <p class="text-[2.4rem] font-semibold leading-none tracking-[-0.03em] text-[#111827] sm:text-[2.9rem] lg:text-[3.2rem]">
                {{ animatedValues[0] }}+
              </p>
              <p class="mx-auto mt-2 max-w-[9rem] text-[0.9rem] leading-[1.45] text-[#4b5563]">
                лет на рынке
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-left', delay: 0.13, mobileAlternate: true, mobileIndex: 5 }"
              class="rounded-[1rem] border border-[#5b6169]/40 bg-white/22 px-4 py-5 text-center shadow-[0_10px_24px_rgba(16,24,40,0.1)] backdrop-blur-[8px]"
            >
              <p class="text-[2.4rem] font-semibold leading-none tracking-[-0.03em] text-[#111827] sm:text-[2.9rem] lg:text-[3.2rem]">
                {{ animatedValues[1] }}+
              </p>
              <p class="mx-auto mt-2 max-w-[9rem] text-[0.9rem] leading-[1.45] text-[#4b5563]">
                реализованных проектов
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-left', delay: 0.21, mobileAlternate: true, mobileIndex: 6 }"
              class="rounded-[1rem] border border-[#5b6169]/40 bg-white/22 px-4 py-5 text-center shadow-[0_10px_24px_rgba(16,24,40,0.1)] backdrop-blur-[8px]"
            >
              <p class="text-[2.4rem] font-semibold leading-none tracking-[-0.03em] text-[#111827] sm:text-[2.9rem] lg:text-[3.2rem]">
                {{ animatedValues[2] }}%
              </p>
              <p class="mx-auto mt-2 max-w-[9rem] text-[0.9rem] leading-[1.45] text-[#4b5563]">
                довольных клиентов
              </p>
            </article>

            <article
              v-reveal="{ type: 'card-left', delay: 0.29, mobileAlternate: true, mobileIndex: 7 }"
              class="rounded-[1rem] border border-[#5b6169]/40 bg-white/22 px-4 py-5 text-center shadow-[0_10px_24px_rgba(16,24,40,0.1)] backdrop-blur-[8px]"
            >
              <p class="text-[2.4rem] font-semibold leading-none tracking-[-0.03em] text-[#111827] sm:text-[2.9rem] lg:text-[3.2rem]">
                {{ animatedValues[3] }}+
              </p>
              <p class="mx-auto mt-2 max-w-[9rem] text-[0.9rem] leading-[1.45] text-[#4b5563]">
                партнеров и поставщиков
              </p>
            </article>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
