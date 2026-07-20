<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRequestModal } from '../composables/useRequestModal'
import { heroContent } from '../data'

const heroPhrases = [
  'ИНЖЕНЕРИЯ. ТОЧНОСТЬ. НАДЁЖНОСТЬ.',
  'МЕТАЛЛОКОНСТРУКЦИИ ЛЮБОЙ СЛОЖНОСТИ',
  'СОВРЕМЕННЫЕ ФАСАДЫ',
  'ПАНОРАМНОЕ ОСТЕКЛЕНИЕ',
  'СТРОИМ ПРОСТРАНСТВО, В КОТОРОМ ХОЧЕТСЯ ЖИТЬ',
]

const activePhraseIndex = ref(0)
const phraseStepMs = 1800
let phraseTimer = null
const isVideoReady = ref(false)
const heroVideoRef = ref(null)
let autoplayRetryTimer = null
let autoplayAttempts = 0

const { openRequestModal } = useRequestModal()

const handlePrimaryAction = () => {
  openRequestModal('hero')
}

const applyAutoplayAttrs = (video) => {
  video.muted = true
  video.defaultMuted = true
  video.playsInline = true
  video.setAttribute('muted', '')
  video.setAttribute('playsinline', '')
  video.setAttribute('webkit-playsinline', '')
}

const isVideoPlaying = (video) => {
  return Boolean(video && !video.paused && !video.ended && video.currentTime > 0)
}

const scheduleAutoplayRetry = (delay = 280) => {
  if (autoplayAttempts >= 5) return

  if (autoplayRetryTimer) {
    clearTimeout(autoplayRetryTimer)
    autoplayRetryTimer = null
  }

  autoplayRetryTimer = window.setTimeout(() => {
    autoplayAttempts += 1
    tryPlayVideo()
  }, delay)
}

const tryPlayVideo = () => {
  const video = heroVideoRef.value
  if (!video) return

  applyAutoplayAttrs(video)
  if (isVideoPlaying(video)) return

  const playPromise = video.play()
  if (playPromise && typeof playPromise.then === 'function') {
    playPromise.catch(() => {
      scheduleAutoplayRetry()
    })
  }
}

const handleVideoCanPlay = () => {
  tryPlayVideo()
}

const handleVideoLoadedData = () => {
  isVideoReady.value = true
  tryPlayVideo()
}

const handleVisibilityOrFocus = () => {
  if (document.visibilityState === 'visible') {
    tryPlayVideo()
  }
}

const handleFirstUserGesture = () => {
  tryPlayVideo()
}

onMounted(() => {
  phraseTimer = setInterval(() => {
    if (activePhraseIndex.value < heroPhrases.length - 1) {
      activePhraseIndex.value += 1
      return
    }

    if (phraseTimer) {
      clearInterval(phraseTimer)
      phraseTimer = null
    }
  }, phraseStepMs)

  tryPlayVideo()
  scheduleAutoplayRetry(420)

  document.addEventListener('visibilitychange', handleVisibilityOrFocus)
  window.addEventListener('focus', handleVisibilityOrFocus)
  window.addEventListener('touchstart', handleFirstUserGesture, { passive: true, once: true })
  window.addEventListener('pointerdown', handleFirstUserGesture, { once: true })
})

onBeforeUnmount(() => {
  if (phraseTimer) {
    clearInterval(phraseTimer)
    phraseTimer = null
  }

  if (autoplayRetryTimer) {
    clearTimeout(autoplayRetryTimer)
    autoplayRetryTimer = null
  }

  document.removeEventListener('visibilitychange', handleVisibilityOrFocus)
  window.removeEventListener('focus', handleVisibilityOrFocus)
  window.removeEventListener('touchstart', handleFirstUserGesture)
  window.removeEventListener('pointerdown', handleFirstUserGesture)
})
</script>

<template>
  <section class="hero-root w-full overflow-hidden border-b border-[#e2e5ea] bg-[#f2f3f5] text-[#181a21]">
    <div class="grid w-full items-stretch overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <div class="z-10 flex min-w-0 w-full items-center px-4 pb-5 pt-[8rem] sm:px-6 sm:pb-6 sm:pt-[8.5rem] lg:justify-center lg:px-10 lg:py-2 xl:px-14">
        <div class="w-full max-w-[42rem]">
          <p
            class="flex flex-wrap gap-x-2 gap-y-1 text-[0.625rem] font-semibold uppercase tracking-[0.18em] text-[#8e929a] sm:text-[0.6875rem]"
          >
            <template
              v-for="(item, index) in heroContent.categories"
              :key="item"
            >
              <span>{{ item }}</span>
              <span v-if="index < heroContent.categories.length - 1">&bull;</span>
            </template>
          </p>

          <h1
            class="mt-3 max-w-[42rem] whitespace-pre-line text-[1.95rem] font-semibold leading-[0.96] tracking-[-0.04em] text-[#14161d] sm:text-[2.6rem] md:text-[3rem] lg:text-[3.35rem]"
          >
            {{ heroContent.title }}
          </h1>

          <p class="mt-3 max-w-[42rem] text-[0.98rem] leading-[1.62] text-[#5d6169] sm:text-[1rem]">
            {{ heroContent.description }}
          </p>

          <button
            type="button"
            class="mt-4 inline-flex items-center gap-3 rounded-xl bg-[#181b24] px-6 py-2.5 text-[0.875rem] font-medium text-white transition duration-200 hover:-translate-y-[1px] hover:bg-black"
            @click="handlePrimaryAction"
          >
            <span>{{ heroContent.primaryAction }}</span>
            <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      </div>

      <div class="relative min-w-0 w-full overflow-hidden bg-[#edf0f3]">
        <div class="relative h-[13.5rem] w-full overflow-hidden sm:h-[16.5rem] md:h-[33.5rem] lg:h-[33.5rem] xl:h-[43rem]">
          <div
            class="absolute inset-0 bg-[linear-gradient(135deg,#edf0f3_0%,#dfe4ea_45%,#eef2f6_100%)] transition-opacity duration-500"
            :class="isVideoReady ? 'opacity-0' : 'opacity-100'"
          />

          <div
            class="pointer-events-none absolute inset-0 z-10 flex items-center justify-center transition-opacity duration-500"
            :class="isVideoReady ? 'opacity-0' : 'opacity-100'"
          >
            <span class="h-8 w-8 animate-spin rounded-full border-2 border-[#c7ced8] border-t-[#7b8798]" />
          </div>

          <video
            ref="heroVideoRef"
            class="block h-full w-full object-cover object-[30%_70%] transition-opacity duration-500 sm:object-[30%_70%] lg:object-[30%_70%]"
            :class="isVideoReady ? 'opacity-100' : 'opacity-0'"
            autoplay
            muted
            playsinline
            webkit-playsinline
            preload="metadata"
            poster="/images/hero.jpg"
            @loadeddata="handleVideoLoadedData"
            @canplay="handleVideoCanPlay"
          >
            <source src="/videos/12345.MP4" type="video/mp4" />
          </video>
        </div>

        <div class="pointer-events-none absolute inset-0 z-30 flex items-center justify-center px-5 sm:px-8 lg:px-10">
          <Transition name="hero-phrase" mode="out-in">
            <p
              :key="activePhraseIndex"
              class="hero-phrase-text max-w-[92%] text-center text-[1.02rem] font-semibold uppercase leading-[1.35] tracking-[0.08em] text-[#d7dde8] sm:text-[1.3rem] md:text-[1.55rem] lg:text-[1.85rem]"
            >
              {{ heroPhrases[activePhraseIndex] }}
            </p>
          </Transition>
        </div>

        <div
          class="pointer-events-none absolute inset-y-0 left-0 hidden w-14 bg-gradient-to-r from-[#f2f3f5] via-[#f2f3f5]/80 to-transparent md:block lg:w-24"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero-root {
  font-family: "Manrope", "Segoe UI", sans-serif;
}

.hero-phrase-text {
  text-shadow:
    0 1px 2px rgba(15, 23, 42, 0.4),
    0 10px 26px rgba(15, 23, 42, 0.4);
}

.hero-phrase-enter-active,
.hero-phrase-leave-active {
  transition:
    opacity 0.52s ease,
    transform 0.52s ease;
}

.hero-phrase-enter-from,
.hero-phrase-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
