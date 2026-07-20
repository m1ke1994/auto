<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { reviews } from '../../data/reviews'

const viewportRef = ref(null)
const isHovered = ref(false)
const isDragging = ref(false)

let autoplayTimer = null
let resumeTimer = null
let startX = 0
let startScrollLeft = 0

const getStep = () => {
  const viewport = viewportRef.value
  if (!viewport) return 0

  const firstSlide = viewport.querySelector('.review-slide')
  const list = viewport.querySelector('.reviews-list')
  if (!firstSlide || !list) return 0

  const gap = parseFloat(window.getComputedStyle(list).columnGap || window.getComputedStyle(list).gap || '0')
  return firstSlide.getBoundingClientRect().width + gap
}

const snapToNearest = () => {
  const viewport = viewportRef.value
  if (!viewport) return

  const step = getStep()
  if (!step) return

  const snapped = Math.round(viewport.scrollLeft / step) * step
  viewport.scrollTo({ left: snapped, behavior: 'smooth' })
}

const goNext = () => {
  const viewport = viewportRef.value
  if (!viewport) return

  const step = getStep()
  if (!step) return

  const maxScroll = viewport.scrollWidth - viewport.clientWidth
  let next = viewport.scrollLeft + step

  if (next >= maxScroll - 2) {
    next = 0
  }

  viewport.scrollTo({ left: next, behavior: 'smooth' })
}

const stopAutoplay = () => {
  if (autoplayTimer) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

const startAutoplay = () => {
  stopAutoplay()

  autoplayTimer = setInterval(() => {
    if (!isHovered.value && !isDragging.value) {
      goNext()
    }
  }, 4300)
}

const scheduleAutoplay = () => {
  if (resumeTimer) {
    clearTimeout(resumeTimer)
    resumeTimer = null
  }

  resumeTimer = setTimeout(() => {
    if (!isHovered.value && !isDragging.value) {
      startAutoplay()
    }
  }, 1800)
}

const onPointerDown = (event) => {
  if (event.pointerType !== 'mouse') return

  const viewport = viewportRef.value
  if (!viewport) return

  isDragging.value = true
  startX = event.clientX
  startScrollLeft = viewport.scrollLeft

  viewport.classList.add('is-dragging')
  viewport.setPointerCapture(event.pointerId)
  stopAutoplay()
}

const onPointerMove = (event) => {
  if (!isDragging.value) return

  const viewport = viewportRef.value
  if (!viewport) return

  const deltaX = event.clientX - startX
  viewport.scrollLeft = startScrollLeft - deltaX
}

const onPointerEnd = (event) => {
  if (!isDragging.value) return

  const viewport = viewportRef.value
  if (!viewport) return

  isDragging.value = false
  viewport.classList.remove('is-dragging')

  if (viewport.hasPointerCapture(event.pointerId)) {
    viewport.releasePointerCapture(event.pointerId)
  }

  snapToNearest()
  scheduleAutoplay()
}

const onMouseEnter = () => {
  isHovered.value = true
  stopAutoplay()
}

const onMouseLeave = () => {
  isHovered.value = false
  scheduleAutoplay()
}

const onTouchStart = () => {
  stopAutoplay()
}

const onTouchEnd = () => {
  scheduleAutoplay()
}

onMounted(async () => {
  await nextTick()
  startAutoplay()
})

onBeforeUnmount(() => {
  stopAutoplay()

  if (resumeTimer) {
    clearTimeout(resumeTimer)
    resumeTimer = null
  }
})
</script>

<template>
  <section id="reviews" class="reviews-root w-full scroll-mt-28 bg-transparent pb-12 pt-4 sm:pb-14 sm:pt-5 lg:pb-16 lg:pt-6">
    <div class="w-full border-0 bg-transparent px-5 py-6 sm:px-8 sm:py-8 lg:px-12 lg:py-10">
      <div class="mx-auto max-w-[58rem] text-center">
        <h2
          v-reveal="{ type: 'title', delay: 0 }"
          class="text-[2rem] font-semibold leading-[1.05] tracking-[-0.03em] text-[#111827] sm:text-[2.7rem] lg:text-[3.2rem]"
        >
          Отзывы наших клиентов
        </h2>
        <p
          v-reveal="{ type: 'title', delay: 0.1 }"
          class="mx-auto mt-4 max-w-[46rem] text-[1rem] leading-[1.72] text-[#4b5563] sm:text-[1.05rem]"
        >
          Мы ценим доверие клиентов и внимательно относимся к качеству каждого реализованного проекта.
        </p>
      </div>

      <div
        ref="viewportRef"
        class="reviews-viewport mt-8 overflow-x-auto sm:mt-9"
        @mouseenter="onMouseEnter"
        @mouseleave="onMouseLeave"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerEnd"
        @pointercancel="onPointerEnd"
        @touchstart.passive="onTouchStart"
        @touchend="onTouchEnd"
      >
        <div class="reviews-list flex gap-4">
          <article
            v-for="(review, index) in reviews"
            :key="review.id"
            v-reveal="{ type: 'review-left', delay: index * 0.07 }"
            class="review-slide flex h-full min-h-[18.5rem] flex-col rounded-[1.25rem] border border-[#5b6169]/28 bg-white/60 p-5  sm:p-6"
          >
            <div class="flex items-start gap-3">
              <img
                :src="review.avatar"
                :alt="review.name"
                class="h-12 w-12 shrink-0 rounded-full border border-[#5b6169]/35 bg-white/75 object-cover"
                loading="lazy"
                decoding="async"
                fetchpriority="low"
                width="48"
                height="48"
              />

              <div class="min-w-0">
                <h3 class="text-[1.02rem] font-semibold leading-[1.2] text-[#111827]">
                  {{ review.name }}
                </h3>
                <p class="mt-1 text-[0.8125rem] leading-[1.45] text-[#6b7280]">
                  {{ review.position }}
                </p>
              </div>
            </div>

            <div class="mt-4 flex items-center gap-1">
              <svg
                v-for="index in 5"
                :key="`${review.id}-${index}`"
                viewBox="0 0 20 20"
                class="h-4 w-4"
                :class="index <= review.rating ? 'text-amber-500' : 'text-slate-300'"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 0 0 .95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 0 0-.364 1.118l1.07 3.292c.3.922-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 0 0-1.176 0l-2.8 2.034c-.784.57-1.838-.196-1.539-1.118l1.07-3.292a1 1 0 0 0-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81H7.03a1 1 0 0 0 .95-.69l1.07-3.292Z" />
              </svg>
            </div>

            <p class="mt-4 text-[0.92rem] leading-[1.72] text-[#4b5563]">
              {{ review.text }}
            </p>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.reviews-root {
  font-family: "Manrope", "Segoe UI", sans-serif;
}

.reviews-viewport {
  scrollbar-width: none;
  scroll-snap-type: x mandatory;
  cursor: grab;
}

.reviews-viewport::-webkit-scrollbar {
  display: none;
}

.reviews-viewport.is-dragging {
  cursor: grabbing;
  user-select: none;
}

.reviews-list {
  width: max-content;
}

.review-slide {
  flex: 0 0 calc(100vw - 2.5rem);
  scroll-snap-align: start;
}

@media (min-width: 640px) {
  .review-slide {
    flex-basis: calc((100vw - 5rem - 1rem) / 2);
  }
}

@media (min-width: 768px) {
  .review-slide {
    flex-basis: calc((100vw - 5rem - 2rem) / 3);
  }
}

@media (min-width: 1024px) {
  .review-slide {
    flex-basis: calc((100vw - 6rem - 2rem) / 3);
  }
}

@media (min-width: 1280px) {
  .review-slide {
    flex-basis: calc((100vw - 6rem - 2rem) / 3);
  }
}
</style>
