<template>
  <div
    ref="reviewsRef"
    class="reviews"
    v-reveal
    @mouseenter="pause"
    @mouseleave="resume"
    @focusin="pause"
    @focusout="resume"
  >
    <div class="reviews__card-wrap">
      <p v-if="loading" class="reviews__status">Загрузка отзывов...</p>
      <p v-else-if="error" class="reviews__status reviews__status--error">{{ error }}</p>
      <p v-else-if="!reviews.length" class="reviews__status">Отзывов пока нет.</p>

      <Transition v-else name="fade-rise" mode="out-in">
        <article
          class="reviews__card glass-card"
          :key="activeReview.id"
          tabindex="0"
        >
          <div class="reviews__avatar">
            <img
              :src="avatarSrc(activeReview.avatar)"
              :alt="`Фото — ${activeReview.name}`"
              loading="lazy"
              decoding="async"
              fetchpriority="low"
              width="64"
              height="64"
              class="img-lazy"
              @load="markImageLoaded"
            />
          </div>

          <div class="reviews__stars" aria-label="Рейтинг">
            <span
              v-for="n in 5"
              :key="n"
              :class="['star', { muted: n > normalizedRating(activeReview.rating) }]"
              aria-hidden="true"
            >
              ★
            </span>
          </div>

          <RichText :content="activeReview.text" class="reviews__text" />

          <div class="reviews__name">{{ activeReview.name }}</div>
          <div class="reviews__meta">{{ activeReview.event_name }} · {{ formatDate(activeReview.date) }}</div>
        </article>
      </Transition>
    </div>

    <div v-if="reviews.length > 1 && !loading && !error" class="reviews__nav">
      <button class="nav-btn" type="button" aria-label="Предыдущий отзыв" @click="prev">
        ‹
      </button>

      <div class="dots" role="tablist" aria-label="Слайды">
        <button
          v-for="(review, idx) in reviews"
          :key="review.id"
          class="dot"
          :class="{ active: idx === activeIndex }"
          type="button"
          @click="goTo(idx)"
          :aria-label="`Слайд ${idx + 1}`"
        ></button>
      </div>

      <button class="nav-btn" type="button" aria-label="Следующий отзыв" @click="next">
        ›
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue"
import { getReviews } from "../../api/reviews"
import RichText from "../ui/RichText.vue";

const DEFAULT_AVATAR = "/avatar.png"

const reviews = ref([])
const loading = ref(false)
const error = ref("")
const activeIndex = ref(0)
const isPaused = ref(false)
const reviewsRef = ref(null)
let timerId = null
let visibilityObserver = null

const activeReview = computed(() => reviews.value[activeIndex.value] || null)

const normalizedRating = (value) => {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return Math.min(5, Math.max(1, Math.round(num)))
}

const formatDate = (value) => {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
}

const avatarSrc = (value) => value || DEFAULT_AVATAR

const next = () => {
  if (!reviews.value.length) return
  activeIndex.value = (activeIndex.value + 1) % reviews.value.length
  restart()
}

const prev = () => {
  if (!reviews.value.length) return
  activeIndex.value = (activeIndex.value - 1 + reviews.value.length) % reviews.value.length
  restart()
}

const goTo = (idx) => {
  activeIndex.value = idx
  restart()
}

const start = () => {
  if (reviews.value.length <= 1) return
  stop()
  timerId = setInterval(() => {
    if (!isPaused.value && reviews.value.length > 1) {
      activeIndex.value = (activeIndex.value + 1) % reviews.value.length
    }
  }, 4500)
}

const stop = () => {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

const pause = () => {
  isPaused.value = true
}

const resume = () => {
  isPaused.value = false
}

const restart = () => {
  stop()
  start()
}

const markImageLoaded = (event) => {
  event.target.classList.add("is-loaded")
}

const load = async () => {
  loading.value = true
  error.value = ""

  try {
    const payload = await getReviews()
    reviews.value = payload
    activeIndex.value = 0
  } catch (err) {
    console.error("[reviews] failed to load", err)
    reviews.value = []
    error.value = "Не удалось загрузить отзывы."
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await load()

  if (typeof window === "undefined") return
  if (!("IntersectionObserver" in window) || !reviewsRef.value) {
    start()
    return
  }

  visibilityObserver = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        start()
      } else {
        stop()
      }
    },
    { rootMargin: "200px 0px", threshold: 0.01 }
  )

  visibilityObserver.observe(reviewsRef.value)
})

onUnmounted(() => {
  stop()
  visibilityObserver?.disconnect()
})
</script>

<style scoped>
.reviews {
  width: 100%;
}

.reviews__card-wrap {
  display: flex;
  justify-content: center;
}

.reviews__status {
  margin: 0;
  padding: 24px;
  text-align: center;
  color: var(--muted);
}

.reviews__status--error {
  color: #b3261e;
}

.reviews__card {
  width: min(900px, 100%);
  padding: 28px 30px;
  display: grid;
  justify-items: center;
  gap: 14px;
  text-align: center;
}

.glass-card {
  border-radius: 26px;
}

.reviews__avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow: 0 10px 20px var(--shadow);
  overflow: hidden;
}

.reviews__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.reviews__stars {
  display: inline-flex;
  gap: 6px;
  font-size: 16px;
  color: var(--primary);
}

.star.muted {
  color: rgba(200, 169, 107, 0.35);
}

.reviews__text {
  font-size: var(--font-size-base);
  font-style: italic;
  color: var(--text);
  margin: 0;
  line-height: 1.6;
}

.reviews__text :deep(p:first-child)::before {
  content: "«";
}

.reviews__text :deep(p:last-child)::after {
  content: "»";
}

.reviews__name {
  font-weight: 600;
  color: var(--text-strong);
}

.reviews__meta {
  font-size: var(--font-size-base);
  color: var(--muted);
}

.reviews__nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
}

.nav-btn {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--card);
  backdrop-filter: blur(12px);
  cursor: pointer;
  color: var(--text);
  box-shadow: 0 10px 20px var(--shadow);
  transition: transform 200ms ease, box-shadow 200ms ease;
  font-size: 20px;
  line-height: 1;
}

.nav-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px var(--shadow);
}

.dots {
  display: inline-flex;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  border: none;
  background: rgba(200, 169, 107, 0.35);
  cursor: pointer;
  transition: width 200ms ease, background 200ms ease;
}

.dot.active {
  width: 18px;
  background: rgba(200, 169, 107, 0.9);
}

.fade-rise-enter-active,
.fade-rise-leave-active {
  transition: opacity 350ms ease, transform 350ms ease;
}

.fade-rise-enter-from,
.fade-rise-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.98);
}

@media (max-width: 720px) {
  .reviews__card {
    padding: 22px 18px;
  }
}
</style>
