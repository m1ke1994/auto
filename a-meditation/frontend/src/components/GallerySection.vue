<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  section: {
    type: Object,
    default: null,
  },
})

const fallbackGalleryItems = [
  {
    src: '/images/DSC08101.JPG',
    alt: 'Атмосфера практики Лила',
    title: 'Пространство встречи',
  },
  {
    src: '/images/2025-02-26 13-06-17.JPG',
    alt: 'Практика и пространство',
    title: 'Тихая практика',
  },
  {
    src: '/images/IMG_5131.JPG',
    alt: 'Детали пространства для практик',
    title: 'Детали пространства',
  },
  {
    src: '/images/Lila_Olga_2.2.poster.jpg',
    alt: 'Глубокое состояние практики',
    title: 'Глубокое состояние',
  },
]

const sectionContent = computed(() => props.section?.content || {})
const galleryTitle = computed(() => sectionContent.value.title || 'Галерея')
const gallerySubtitle = computed(() => sectionContent.value.subtitle || 'Визуальная история')
const galleryDescription = computed(
  () => sectionContent.value.description || 'Атмосфера практик, встреч и пространства',
)
const galleryItems = computed(() => {
  const items = sectionContent.value.items
  if (!Array.isArray(items) || items.length === 0) {
    return fallbackGalleryItems
  }

  return items
    .filter((item) => item && item.src)
    .map((item) => ({
      src: item.src,
      alt: item.alt || item.title || 'Галерея',
      title: item.title || 'Изображение',
    }))
})

const selectedMedia = ref(null)
let previousBodyOverflow = ''

const openMedia = (item) => {
  selectedMedia.value = item
  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
}

const closeMedia = () => {
  selectedMedia.value = null
  document.body.style.overflow = previousBodyOverflow
}

const handleKeydown = (event) => {
  if (event.key === 'Escape' && selectedMedia.value) {
    closeMedia()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = previousBodyOverflow
})
</script>

<template>
  <section
    id="gallery"
    class="bg-[#F8F3EA] px-6 py-16 text-[#24231F] md:px-8 md:py-20"
  >
    <div class="mx-auto max-w-[1200px]">
      <div class="mx-auto max-w-[760px] text-center">
        <p class="mb-3 text-xs font-medium uppercase tracking-[0.28em] text-[#8B7449]/60">
          {{ gallerySubtitle }}
        </p>

        <h2 class="text-4xl font-semibold leading-tight tracking-[0.01em] text-[#24231F] sm:text-5xl md:text-6xl">
          {{ galleryTitle }}
        </h2>

        <p class="mt-5 text-lg leading-8 text-stone-600 sm:text-xl sm:leading-9">
          {{ galleryDescription }}
        </p>
      </div>

      <div class="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article
          v-for="item in galleryItems"
          :key="item.src"
          class="group relative h-[280px] overflow-hidden rounded-3xl bg-[#FBF7EF] shadow-sm transition duration-300 hover:-translate-y-1 hover:shadow-[0_24px_70px_rgba(0,0,0,0.12)] sm:h-[300px] lg:h-[280px]"
        >
          <button
            type="button"
            class="h-full w-full cursor-zoom-in text-left"
            :aria-label="`Открыть фото: ${item.title}`"
            @click="openMedia(item)"
          >
            <img
              :src="item.src"
              :alt="item.alt"
              class="h-full w-full object-cover transition duration-500 group-hover:scale-[1.04]"
              loading="lazy"
              decoding="async"
            >

            <div class="absolute inset-0 flex items-center justify-center bg-black/35 px-6 text-center opacity-0 transition duration-300 group-hover:opacity-100">
              <h3 class="text-lg font-semibold leading-7 text-white drop-shadow-sm">
                {{ item.title }}
              </h3>
            </div>
          </button>
        </article>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="media-modal">
        <div
          v-if="selectedMedia"
          class="fixed inset-0 z-[999] flex items-center justify-center bg-black/75 p-5 backdrop-blur-md sm:p-6"
          @click="closeMedia"
        >
          <button
            type="button"
            class="absolute right-4 top-4 z-10 flex h-12 w-12 items-center justify-center rounded-full border border-white/15 bg-white/10 text-white shadow-2xl backdrop-blur-xl transition duration-300 hover:scale-105 hover:bg-white hover:text-[#24231F] sm:right-6 sm:top-6"
            aria-label="Закрыть просмотр"
            @click.stop="closeMedia"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M18 6 6 18" />
              <path d="m6 6 12 12" />
            </svg>
          </button>

          <img
            :src="selectedMedia.src"
            :alt="selectedMedia.alt"
            class="max-h-[88vh] max-w-[calc(100vw-32px)] rounded-2xl object-contain shadow-[0_30px_120px_rgba(0,0,0,0.55)] sm:max-h-[92vh] sm:max-w-[92vw]"
            decoding="async"
            @click.stop
          >
        </div>
      </Transition>
    </Teleport>
  </section>
</template>

<style scoped>
.media-modal-enter-active,
.media-modal-leave-active {
  transition: opacity 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.media-modal-enter-from,
.media-modal-leave-to {
  opacity: 0;
}

.media-modal-enter-active img,
.media-modal-leave-active img {
  transition:
    opacity 300ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.media-modal-enter-from img,
.media-modal-leave-to img {
  opacity: 0;
  transform: scale(0.96);
}
</style>
