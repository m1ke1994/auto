<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { CheckCircle2, LayoutTemplate, Loader2 } from '@lucide/vue'

const props = defineProps({
  active: { type: Boolean, default: false },
})

const steps = [
  'Анализируем категорию бизнеса',
  'Подбираем подходящий дизайн',
  'Собираем структуру страниц',
  'Добавляем данные компании',
  'Настраиваем адаптивную версию',
  'Подготавливаем предпросмотр',
  'Ваш сайт готов',
]

const index = ref(0)
let timer = null

const progress = computed(() => Math.min(96, Math.round(((index.value + 1) / steps.length) * 100)))

function start() {
  stop()
  index.value = 0
  timer = window.setInterval(() => {
    if (index.value < steps.length - 2) index.value += 1
  }, 900)
}

function stop() {
  if (timer) window.clearInterval(timer)
  timer = null
}

onMounted(() => {
  if (props.active) start()
})

onUnmounted(stop)
</script>

<template>
  <section class="generation-screen" aria-live="polite" aria-busy="true">
    <div class="generation-shell">
      <div class="generation-visual" aria-hidden="true">
        <LayoutTemplate :size="44" />
        <div class="skeleton-page">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
      <p class="eyebrow">Создание сайта</p>
      <h2>{{ steps[index] }}</h2>
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: `${progress}%` }" />
      </div>
      <ol>
        <li v-for="(step, stepIndex) in steps" :key="step" :class="{ done: stepIndex < index, active: stepIndex === index }">
          <CheckCircle2 v-if="stepIndex < index" :size="17" />
          <Loader2 v-else-if="stepIndex === index" :size="17" class="spin" />
          <span v-else />
          {{ step }}
        </li>
      </ol>
    </div>
  </section>
</template>

<style scoped>
.generation-screen {
  display: grid;
  min-height: calc(100vh - 9rem);
  place-items: center;
}

.generation-shell {
  width: min(100%, 42rem);
  border: 1px solid rgba(101, 71, 232, 0.14);
  border-radius: 1.25rem;
  background: #fff;
  padding: 2rem;
  box-shadow: 0 22px 60px rgba(32, 40, 70, 0.12);
}

.generation-visual {
  display: grid;
  grid-template-columns: 4rem 1fr;
  gap: 1rem;
  align-items: center;
  color: #6547e8;
}

.skeleton-page {
  display: grid;
  gap: 0.6rem;
}

.skeleton-page span {
  height: 0.85rem;
  border-radius: 999px;
  background: linear-gradient(90deg, #eef2ff, #f8fafc, #eef2ff);
  animation: shimmer 1.2s infinite linear;
}

.skeleton-page span:first-child {
  width: 72%;
}

.skeleton-page span:nth-child(3) {
  width: 86%;
}

.skeleton-page span:last-child {
  width: 58%;
}

h2 {
  margin: 1rem 0;
  color: #17223b;
  font-size: clamp(1.45rem, 3vw, 2.2rem);
  font-weight: 850;
}

.progress-track {
  height: 0.7rem;
  overflow: hidden;
  border-radius: 999px;
  background: #eef2ff;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6547e8, #10b981);
  transition: width 0.45s ease;
}

ol {
  display: grid;
  gap: 0.65rem;
  margin: 1.25rem 0 0;
  padding: 0;
  list-style: none;
}

li {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #64748b;
  font-size: 0.95rem;
  font-weight: 650;
}

li > span {
  width: 17px;
  height: 17px;
  border: 2px solid #cbd5e1;
  border-radius: 999px;
}

li.done,
li.active {
  color: #17223b;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes shimmer {
  100% {
    filter: hue-rotate(25deg);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
