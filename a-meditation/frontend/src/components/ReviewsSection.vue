<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  section: {
    type: Object,
    default: null,
  },
})

const sectionRef = ref(null)
const isVisible = ref(false)
const activeIndex = ref(0)

const sectionContent = computed(() => props.section?.content || {})
const reviewsTag = computed(() => sectionContent.value.subtitle || 'Реальные впечатления')
const reviewsTitle = computed(() => sectionContent.value.title || 'Отзывы участников')
const reviewsDescription = computed(
  () => sectionContent.value.description || 'Истории людей, которые прошли практику и поделились своим опытом.',
)
const reviewsCtaText = computed(() => sectionContent.value.button_text || 'Читать больше отзывов')
const reviewsUrl = computed(() => sectionContent.value.button_link || 'https://t.me/leelabirdcase')

const fallbackReviews = [
  {
    name: 'Участница игры',
    date: 'Отзыв из Telegram',
    avatar: '/images/IMG_1245.JPG',
    text: 'Я все хотела написать отзыв об игре. Да вот только игра — это не какая-то точка, в которую ты пришел и всё разрешилось. Это мыслительный процесс, уходящий глубоко в душу, где не все и не всегда на своих местах. Писать отзыв на эту игру все равно что писать отзыв на жизнь, которую еще живешь. Я пока что в процессе проживания, и это временами тяжело, а временами прекрасно. А тебе большое спасибо как проводнику. Ты здорово ведешь туда, куда надо, давая при этом выбор.',
  },
  {
    name: 'Участница игры',
    date: 'Отзыв из Telegram',
    avatar: '/images/IMG_1246.JPG',
    text: 'Ольга, просто нет слов. Меня переполняют эмоции, я пошла гулять, дышать, осознавать. Инсайты меня будут догонять ещё несколько дней точно. Спасибо огромное за такую комфортную игру! Обсуждали довольно личные вещи, но мне было комфортно проговаривать их. Ты всё мне разъясняла, отвечала на вопросы, для меня это важно. Платформа тоже хорошая, красивая. В общем, я исполнила свою мечту — поиграть в Лилу.',
  },
  {
    name: 'Участница игры',
    date: 'Отзыв из Telegram',
    avatar: '/images/IMG_1249.JPG',
    text: 'Если коротко — это было волшебно. А если чуть подробнее — 4 часа пролетели как одно дыхание. Игра помогла не просто «о чём-то задуматься», а реально подсветила глубинные вещи: и то, что тормозит, и то, куда стоит смело идти. Каждый ход был как разговор с собой — честный, порой неожиданный. А Ольга в этом процессе была не просто ведущей, а надёжным проводником. Очень тонко чувствует, мягко направляет, но при этом уверенно держит пространство. Благодаря ей я начала видеть и чувствовать то, что раньше оставалось где-то в тени. Для меня это была встреча с собой настоящей. Я почувствовала свою эмоциональность, которую обычно держу в узде. А тут — как будто можно было быть собой на 100%. Спасибо тебе, Оля, за эту атмосферу, энергию и чуткость. Игра дала мне ответы, которые я долго искала — и я точно хочу ещё.',
  },
  {
    name: 'Участница игры',
    date: 'Отзыв из Telegram',
    avatar: '/images/IMG_1988.JPG',
    text: 'Игра Лила стала для меня очень глубоким опытом. В процессе я увидела важные внутренние связи, которые раньше не замечала. Было спокойно, бережно и честно. Спасибо Ольге за пространство, в котором можно было говорить открыто, чувствовать себя в безопасности и постепенно приходить к ясности.',
  },
]

const reviews = computed(() => {
  const items = sectionContent.value.items
  if (!Array.isArray(items) || items.length === 0) {
    return fallbackReviews
  }

  const mapped = items
    .filter((item) => item && item.text)
    .map((item) => ({
      name: item.name || 'Участник практики',
      date: item.date || 'Отзыв',
      avatar: item.avatar || '/images/IMG_1245.JPG',
      text: item.text,
    }))

  return mapped.length ? mapped : fallbackReviews
})

const activeReview = computed(() => reviews.value[activeIndex.value] || reviews.value[0])

let observer
let touchStartX = 0
let touchDeltaX = 0

const nextReview = () => {
  activeIndex.value = (activeIndex.value + 1) % reviews.value.length
}

const prevReview = () => {
  activeIndex.value = activeIndex.value === 0 ? reviews.value.length - 1 : activeIndex.value - 1
}

const setReview = (index) => {
  activeIndex.value = index
}

const handleTouchStart = (event) => {
  touchStartX = event.touches[0]?.clientX ?? 0
  touchDeltaX = 0
}

const handleTouchMove = (event) => {
  const currentX = event.touches[0]?.clientX ?? touchStartX
  touchDeltaX = currentX - touchStartX
}

const handleTouchEnd = () => {
  if (Math.abs(touchDeltaX) < 48) return

  if (touchDeltaX < 0) {
    nextReview()
  } else {
    prevReview()
  }

  touchStartX = 0
  touchDeltaX = 0
}

onMounted(() => {
  if (!sectionRef.value) return

  if (!('IntersectionObserver' in window)) {
    isVisible.value = true
    return
  }

  observer = new IntersectionObserver(
    ([entry]) => {
      if (!entry.isIntersecting) return

      isVisible.value = true
      observer?.disconnect()
    },
    {
      rootMargin: '0px 0px -16% 0px',
      threshold: 0.14,
    },
  )

  observer.observe(sectionRef.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<template>
  <section
    id="reviews"
    ref="sectionRef"
    class="relative scroll-mt-24 overflow-hidden bg-[#F8F3EA] px-5 py-16 text-[#24231F] sm:px-6 md:px-8 md:py-24"
  >
    <div class="pointer-events-none absolute -left-36 top-10 h-80 w-80 rounded-full bg-white/75 blur-3xl" />
    <div class="pointer-events-none absolute -right-40 bottom-0 h-96 w-96 rounded-full bg-[#8B7449]/35 blur-3xl" />

    <div class="relative mx-auto max-w-[1120px]">
      <div
        class="mx-auto max-w-[760px] text-center transition-all duration-1000 ease-out"
        :class="isVisible ? 'translate-y-0 opacity-100 blur-0' : 'translate-y-6 opacity-0 blur-sm'"
      >
        <span class="mb-4 inline-flex rounded-full border border-[#8B7449]/40 bg-white/70 px-4 py-2 text-[11px] font-medium uppercase tracking-[0.24em] text-[#8B7449]">
          {{ reviewsTag }}
        </span>

        <h2 class="text-3xl font-semibold leading-tight tracking-[-0.035em] text-[#24231F] sm:text-4xl md:text-5xl">
          {{ reviewsTitle }}
        </h2>

        <p class="mt-4 text-base leading-7 text-stone-600 sm:text-lg sm:leading-8">
          {{ reviewsDescription }}
        </p>
      </div>

      <div
        class="relative mx-auto mt-10 max-w-[900px] transition-all delay-150 duration-1000 ease-out"
        :class="isVisible ? 'translate-y-0 opacity-100 blur-0' : 'translate-y-8 opacity-0 blur-sm'"
        @touchstart.passive="handleTouchStart"
        @touchmove.passive="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <button
          type="button"
          class="absolute left-0 top-1/2 z-10 hidden h-12 w-12 -translate-x-16 -translate-y-1/2 items-center justify-center rounded-full border border-black/10 bg-white text-2xl text-[#8B7449] shadow-lg transition hover:-translate-x-[4.25rem] hover:bg-[#24231F] hover:text-white md:flex"
          aria-label="Предыдущий отзыв"
          @click="prevReview"
        >
          ‹
        </button>

        <Transition name="review-fade" mode="out-in">
          <article
            :key="`${activeReview.name}-${activeIndex}`"
            class="relative flex min-h-[430px] flex-col overflow-hidden rounded-[2rem] border border-white/75 bg-white/82 p-6 shadow-[0_26px_80px_rgba(45,35,20,0.12)] backdrop-blur-xl sm:p-8 md:min-h-[460px] md:p-10"
          >
            <div class="pointer-events-none absolute -right-16 -top-16 h-44 w-44 rounded-full bg-[#8B7449]/70" />

            <div class="relative flex items-center gap-4">
              <img
                :src="activeReview.avatar"
                :alt="activeReview.name"
                class="h-14 w-14 rounded-full object-cover ring-1 ring-black/10 md:h-16 md:w-16"
                loading="lazy"
                decoding="async"
              >

              <div>
                <h3 class="text-lg font-semibold leading-7 text-[#24231F] md:text-xl">
                  {{ activeReview.name }}
                </h3>

                <p class="text-sm leading-5 text-stone-500">
                  {{ activeReview.date }}
                </p>
              </div>
            </div>

            <div class="review-scroll relative mt-7 max-h-[260px] flex-1 overflow-y-auto pr-3 md:max-h-[285px]">
              <p class="text-[17px] leading-8 text-stone-700 md:text-xl md:leading-9">
                {{ activeReview.text }}
              </p>
            </div>

            <div class="relative mt-7 h-px w-full bg-[#8B7449]/30" />

            <div class="relative mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-xs font-medium uppercase tracking-[0.22em] text-stone-500">
                {{ activeIndex + 1 }} / {{ reviews.length }}
              </p>

              <a
                :href="reviewsUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center justify-center gap-2 rounded-full bg-[#24231F] px-5 py-3 text-sm font-medium text-white shadow-lg shadow-[#24231F]/15 transition duration-300 hover:-translate-y-0.5 hover:bg-[#8B7449] hover:shadow-[0_16px_40px_rgba(139,116,73,0.18)]"
              >
                {{ reviewsCtaText }}
                <svg
                  viewBox="0 0 24 24"
                  class="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path d="M7 17 17 7" />
                  <path d="M8 7h9v9" />
                </svg>
              </a>
            </div>
          </article>
        </Transition>

        <button
          type="button"
          class="absolute right-0 top-1/2 z-10 hidden h-12 w-12 translate-x-16 -translate-y-1/2 items-center justify-center rounded-full border border-black/10 bg-white text-2xl text-[#8B7449] shadow-lg transition hover:translate-x-[4.25rem] hover:bg-[#24231F] hover:text-white md:flex"
          aria-label="Следующий отзыв"
          @click="nextReview"
        >
          ›
        </button>
      </div>

      <div class="mt-7 flex items-center justify-center gap-2">
        <button
          v-for="(_, index) in reviews"
          :key="index"
          type="button"
          class="h-2.5 rounded-full transition-all duration-300"
          :class="activeIndex === index ? 'w-8 bg-[#8B7449]' : 'w-2.5 bg-black/20 hover:bg-[#8B7449]/45'"
          :aria-label="`Показать отзыв ${index + 1}`"
          @click="setReview(index)"
        />
      </div>

      <p class="mt-4 text-center text-xs font-medium uppercase tracking-[0.22em] text-stone-500 md:hidden">
        листайте отзывы
      </p>
    </div>
  </section>
</template>

<style scoped>
.review-fade-enter-active,
.review-fade-leave-active {
  transition:
    opacity 0.45s ease,
    transform 0.45s ease,
    filter 0.45s ease;
}

.review-fade-enter-from {
  opacity: 0;
  transform: translateY(18px) scale(0.98);
  filter: blur(8px);
}

.review-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
  filter: blur(8px);
}

.review-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(139, 116, 73, 0.45) transparent;
}

.review-scroll::-webkit-scrollbar {
  width: 6px;
}

.review-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.review-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(139, 116, 73, 0.42);
}
</style>
