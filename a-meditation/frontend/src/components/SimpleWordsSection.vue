<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  section: {
    type: Object,
    default: null,
  },
})

const activeSimpleIndex = ref(0)
const activeProcessIndex = ref(0)
const simpleScrollRef = ref(null)
const processScrollRef = ref(null)

const fallbackProcessCards = [
  {
    icon: '01',
    title: 'Без спешки',
    text: 'Есть возможность проходить игру до полного прохождения.',
  },
  {
    icon: '02',
    title: 'С мастером игры',
    text: 'Глубокие практики Лилы простым и понятным языком.',
  },
  {
    icon: '03',
    title: 'Подберём дату',
    text: 'Удобные дата и время игры в группе или индивидуально.',
  },
  {
    icon: '04',
    title: 'Большое поле',
    text: 'Играющий перемещается по клеткам поля своими ногами.',
  },
]

const fallbackSimpleCards = [
  {
    number: '01',
    title: 'Что такое Лила?',
    text: 'Лила — древняя трансформационная игра, где человек формулирует запрос и проходит путь по игровому полю. Каждый ход помогает посмотреть на ситуацию глубже и честнее.',
  },
  {
    number: '02',
    title: 'Как проходит игра?',
    text: 'Игрок движется по клеткам поля, а проводник помогает расшифровать значения состояний и связать их с реальной жизнью, вопросом или внутренним выбором.',
  },
  {
    number: '03',
    title: 'Для чего это нужно?',
    text: 'Игра помогает увидеть скрытые причины напряжения, найти опору, принять решение и почувствовать больше ясности в себе.',
  },
  {
    number: '04',
    title: 'Что получают игроки?',
    text: `Уверенность, ясность, отношения, работу, жизнь мечты.
Вы точно узнаете, чего на самом деле хотите, раскроете свой потенциал и запустите процесс изменений в свою жизнь`,
  },
]

const sectionContent = computed(() => props.section?.content || {})
const simpleEyebrow = computed(() => sectionContent.value.eyebrow || 'Понятно и бережно')
const simpleTitle = computed(() => sectionContent.value.title || 'Лила простыми словами')
const simpleDescription = computed(
  () => sectionContent.value.description || 'Игра Лила — это не гадание и не случайный набор ходов. Это мягкий способ увидеть свои внутренние состояния, вопросы и повторяющиеся сценарии через игровое поле.',
)
const simpleMobileLabel = computed(() => sectionContent.value.mobile_cards_label || 'Листайте карточки')
const processEyebrow = computed(() => sectionContent.value.process_eyebrow || 'Процесс')
const processTitle = computed(() => sectionContent.value.process_title || 'Как проходит Лила?')
const processMobileLabel = computed(() => sectionContent.value.mobile_process_label || 'Свайпните процесс')

const simpleCards = computed(() => {
  const cards = sectionContent.value.cards
  if (!Array.isArray(cards) || cards.length === 0) return fallbackSimpleCards

  const mapped = cards
    .filter((card) => card && (card.title || card.text))
    .map((card, index) => ({
      number: card.number || String(index + 1).padStart(2, '0'),
      title: card.title || '',
      text: card.text || '',
    }))

  return mapped.length ? mapped : fallbackSimpleCards
})

const processCards = computed(() => {
  const cards = sectionContent.value.process_cards
  if (!Array.isArray(cards) || cards.length === 0) return fallbackProcessCards

  const mapped = cards
    .filter((card) => card && (card.title || card.text))
    .map((card, index) => ({
      icon: card.icon || String(index + 1).padStart(2, '0'),
      title: card.title || '',
      text: card.text || '',
    }))

  return mapped.length ? mapped : fallbackProcessCards
})

const simpleProgress = computed(() => activeSimpleIndex.value + 1)
const processProgress = computed(() => activeProcessIndex.value + 1)

const updateActiveIndex = (event, type) => {
  const container = event.target
  const cards = [...container.querySelectorAll('[data-swipe-card]')]
  const containerCenter = container.scrollLeft + container.clientWidth / 2

  const nearestIndex = cards.reduce((nearest, card, index) => {
    const cardCenter = card.offsetLeft + card.clientWidth / 2
    const distance = Math.abs(containerCenter - cardCenter)

    return distance < nearest.distance ? { index, distance } : nearest
  }, { index: 0, distance: Number.POSITIVE_INFINITY }).index

  if (type === 'simple') {
    activeSimpleIndex.value = nearestIndex
  }

  if (type === 'process') {
    activeProcessIndex.value = nearestIndex
  }
}

const scrollToCard = (type, index) => {
  const container = type === 'simple' ? simpleScrollRef.value : processScrollRef.value
  if (!container) return

  const cards = container.querySelectorAll('[data-swipe-card]')
  cards[index]?.scrollIntoView({
    behavior: 'smooth',
    block: 'nearest',
    inline: 'center',
  })
}
</script>

<template>
  <section
    id="simple-words"
    class="scroll-mt-24 bg-white px-6 py-20 text-[#242424] md:px-8 md:py-24"
  >
    <div class="mx-auto max-w-[1200px]">
      <div>
        <div class="mx-auto max-w-[780px] text-center">
          <p class="mb-4 text-xs font-medium uppercase tracking-[0.28em] text-black/45">
            {{ simpleEyebrow }}
          </p>

          <h2 class="text-4xl font-semibold leading-tight tracking-[0.01em] text-[#20201d] sm:text-5xl md:text-6xl">
            {{ simpleTitle }}
          </h2>

          <p class="mt-5 text-lg leading-8 text-stone-600 sm:text-xl sm:leading-9">
            {{ simpleDescription }}
          </p>
        </div>

        <div class="mt-12 hidden gap-5 md:grid md:grid-cols-2 lg:grid-cols-4">
          <article
            v-for="card in simpleCards"
            :key="card.number"
            class="group relative min-h-[320px] overflow-hidden rounded-2xl border border-black/10 bg-white p-6 shadow-sm transition duration-300 hover:-translate-y-1.5 hover:shadow-[0_24px_60px_rgba(0,0,0,0.1)]"
          >
            <div class="mb-8 flex items-center justify-between">
              <span class="text-xs font-semibold tracking-[0.22em] text-black/35">
                {{ card.number }}
              </span>
              <span class="h-2 w-2 rounded-full bg-[#1E7D8B]/35 transition group-hover:bg-[#0C5865]/70" />
            </div>

            <h3 class="text-xl font-semibold leading-7 text-[#24231f]">
              {{ card.title }}
            </h3>
            <p class="mt-5 text-base leading-7 text-stone-600">
              {{ card.text }}
            </p>
          </article>
        </div>

        <div class="mt-10 md:hidden">
          <div class="mb-4 flex items-center justify-between">
            <p class="text-xs font-medium uppercase tracking-[0.22em] text-[#1E7D8B]/70">
              {{ simpleMobileLabel }}
            </p>
            <div class="flex items-center gap-2 text-xs text-stone-500">
              <span>{{ simpleProgress }}</span>
              <span>/</span>
              <span>{{ simpleCards.length }}</span>
              <span class="ml-1 animate-pulse text-lg">→</span>
            </div>
          </div>

          <div
            ref="simpleScrollRef"
            class="cards-scroll -mx-6 flex snap-x snap-mandatory gap-4 overflow-x-auto px-6 pb-5"
            @scroll.passive="updateActiveIndex($event, 'simple')"
          >
            <article
              v-for="card in simpleCards"
              :key="card.number"
              data-swipe-card
              class="min-h-[340px] w-[86vw] shrink-0 snap-center rounded-3xl border border-black/10 bg-white p-6 shadow-[0_20px_55px_rgba(0,0,0,0.08)]"
            >
              <div class="mb-8 flex items-center justify-between">
                <span class="text-xs font-semibold tracking-[0.22em] text-black/35">
                  {{ card.number }}
                </span>
                <span class="h-2 w-2 rounded-full bg-[#1E7D8B]/60" />
              </div>

              <h3 class="text-2xl font-semibold leading-8 text-[#24231f]">
                {{ card.title }}
              </h3>
              <p class="mt-5 text-base leading-7 text-stone-600">
                {{ card.text }}
              </p>
            </article>
          </div>

          <div class="mt-2 flex justify-center gap-2">
            <button
              v-for="(_, index) in simpleCards"
              :key="index"
              type="button"
              class="h-2.5 rounded-full transition-all duration-300"
              :class="activeSimpleIndex === index ? 'w-8 bg-[#1E7D8B]' : 'w-2.5 bg-black/20 hover:bg-[#0C5865]/45'"
              :aria-label="`Показать карточку ${index + 1}`"
              @click="scrollToCard('simple', index)"
            />
          </div>
        </div>
      </div>

      <div class="mt-20 md:mt-24">
        <div class="mx-auto max-w-[760px] text-center">
          <p class="text-xs font-medium uppercase tracking-[0.28em] text-black/45">
            {{ processEyebrow }}
          </p>

          <h2 class="mt-3 text-3xl font-semibold uppercase leading-tight tracking-[0.08em] text-[#20201d] sm:text-4xl md:text-5xl">
            {{ processTitle }}
          </h2>
        </div>

        <div class="mt-12 hidden gap-5 md:grid md:grid-cols-2 lg:grid-cols-4">
          <article
            v-for="card in processCards"
            :key="card.title"
            class="group min-h-[240px] rounded-2xl border border-black/10 bg-white p-6 text-center shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-[0_22px_55px_rgba(0,0,0,0.09)]"
          >
            <div class="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-full border border-black/10 bg-white text-xs font-semibold tracking-[0.18em] text-[#1E7D8B] shadow-sm transition group-hover:border-[#0C5865]/25 group-hover:text-[#0C5865]">
              {{ card.icon }}
            </div>
            <h3 class="text-lg font-semibold leading-7 text-[#24231f]">
              {{ card.title }}
            </h3>
            <p class="mt-4 text-sm leading-6 text-stone-600">
              {{ card.text }}
            </p>
          </article>
        </div>

        <div class="mt-10 md:hidden">
          <div class="mb-4 flex items-center justify-between">
            <p class="text-xs font-medium uppercase tracking-[0.22em] text-[#1E7D8B]/70">
              {{ processMobileLabel }}
            </p>
            <div class="flex items-center gap-2 text-xs text-stone-500">
              <span>{{ processProgress }}</span>
              <span>/</span>
              <span>{{ processCards.length }}</span>
              <span class="ml-1 animate-pulse text-lg">→</span>
            </div>
          </div>

          <div
            ref="processScrollRef"
            class="cards-scroll -mx-6 flex snap-x snap-mandatory gap-4 overflow-x-auto px-6 pb-5"
            @scroll.passive="updateActiveIndex($event, 'process')"
          >
            <article
              v-for="card in processCards"
              :key="card.title"
              data-swipe-card
              class="min-h-[260px] w-[86vw] shrink-0 snap-center rounded-3xl border border-black/10 bg-white p-7 text-center shadow-[0_20px_55px_rgba(0,0,0,0.08)]"
            >
              <div class="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-black/10 bg-white text-xs font-semibold tracking-[0.18em] text-[#1E7D8B] shadow-sm">
                {{ card.icon }}
              </div>
              <h3 class="text-xl font-semibold leading-7 text-[#24231f]">
                {{ card.title }}
              </h3>
              <p class="mt-4 text-base leading-7 text-stone-600">
                {{ card.text }}
              </p>
            </article>
          </div>

          <div class="mt-2 flex justify-center gap-2">
            <button
              v-for="(_, index) in processCards"
              :key="index"
              type="button"
              class="h-2.5 rounded-full transition-all duration-300"
              :class="activeProcessIndex === index ? 'w-8 bg-[#1E7D8B]' : 'w-2.5 bg-black/20 hover:bg-[#0C5865]/45'"
              :aria-label="`Показать этап ${index + 1}`"
              @click="scrollToCard('process', index)"
            />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.cards-scroll {
  scrollbar-width: none;
}

.cards-scroll::-webkit-scrollbar {
  display: none;
}
</style>
