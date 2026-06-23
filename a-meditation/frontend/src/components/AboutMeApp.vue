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
const sectionContent = computed(() => props.section?.content || {})
const imageUrl = computed(() => sectionContent.value.image || '/images/2025-02-26 12-35-42.JPG')
const imageAlt = computed(() => sectionContent.value.image_alt || 'Проводник игры Лила Ольга Бердникова')
const guideTag = computed(() => sectionContent.value.tag || 'Проводник игры Лила')
const guideTitle = computed(() => sectionContent.value.subtitle || 'Ольга Бердникова')
const guideBrand = computed(() => sectionContent.value.brand || 'Leelabird')
const guideCaption = computed(() => sectionContent.value.description || 'Практик осознанности, медитации и Игры Лила')

const metricIcons = [
  'M12 3.5c4.1 2.9 6.5 6.2 6.5 9.8a6.5 6.5 0 0 1-13 0c0-3.6 2.4-6.9 6.5-9.8Z M9.2 13.1l1.8 1.8 3.9-4.7',
  'M7 6.8h10 M7 11.8h10 M7 16.8h6 M5.5 3.5h13a1 1 0 0 1 1 1v15l-3-2-3 2-3-2-3 2-3-2-3 2v-15a1 1 0 0 1 1-1Z',
  'M12 20c4.5-2.6 7-5.5 7-9.2A4.1 4.1 0 0 0 12 7a4.1 4.1 0 0 0-7 3.8C5 14.5 7.5 17.4 12 20Z',
  'M12 3.5v2.2 M12 18.3v2.2 M5.7 5.7l1.5 1.5 M16.8 16.8l1.5 1.5 M3.5 12h2.2 M18.3 12h2.2 M5.7 18.3l1.5-1.5 M16.8 7.2l1.5-1.5 M8.5 12a3.5 3.5 0 1 0 7 0 3.5 3.5 0 0 0-7 0Z',
]
const fallbackMetrics = [
  { value: '100%', label: 'экологичное ведение' },
  { value: '2000+', label: 'проведённых игр' },
  { value: 'мягко', label: 'без давления' },
  { value: 'ясно', label: 'простым языком' },
]
const fallbackIntroParagraphs = [
  'Пройдя глубокий опыт випассаны — специального ретрита, проведенного в полном молчании, аскетизме и медитациях, в 2022 году на день рождения в подарок получила участие в Игре Лила.',
  'После игры во мне произошла сильная трансформация. События, отыгранные на поле, разворачивались четыре месяца, меняя вектор моей жизни. Уходило лишнее, приходило нужное.',
  'Но самое главное — произошло узнавание себя как Проводника Лилы.',
]
const fallbackExpandedParagraphs = [
  'Я прошла обучение в международной школе OMKARA и с тех пор веду Игру на постоянной основе, являюсь игропрактиком на фестивалях самопознания День Йоги, День Индии, Этно космос и других.',
]
const fallbackResults = [
  'Возобновили или с нуля создали доходные проекты по сердцу, в которые до этого не верили',
  'Переехали в место, подходящее для развития и счастливой жизни',
  'Выстроили гармоничные отношения с близкими, сохраняя свои интересы',
  'Научились кайфовать от себя и жизни и похудели на 8 кг без диет и стресса',
]
const fallbackFinalParagraphs = [
  'Исповедую идею баланса, ответственного отношения к жизни, сострадания, красоты и здорового юмора.',
  'Называю себя чутким, но четким проводником: веду очень мягко, без насилия, чувствую поле, но при необходимости крепким словцом верну в реальность.',
  'Важно! На поле Лилы есть клеточка Дана — Щедрость. Она поднимает игрока по стреле в состояние баланса.',
  'Играя в Лилу со мной, вы автоматически участвуете в благотворительности: 10% после каждой игры я перевожу на помощь тем, кому она необходима.',
]

function textList(value, fallback) {
  if (!Array.isArray(value) || value.length === 0) return fallback
  const items = value
    .map((item) => (typeof item === 'string' ? item : item?.text))
    .filter(Boolean)
  return items.length ? items : fallback
}

const introParagraphs = computed(() => textList(sectionContent.value.intro_paragraphs, fallbackIntroParagraphs))
const expandedParagraphs = computed(() => textList(sectionContent.value.expanded_paragraphs, fallbackExpandedParagraphs))
const results = computed(() => textList(sectionContent.value.results, fallbackResults))
const finalParagraphs = computed(() => textList(sectionContent.value.final_paragraphs, fallbackFinalParagraphs))
const resultsTitle = computed(() => sectionContent.value.results_title || '250+ человек уже прошли со мной свою трансформацию:')
const closingText = computed(
  () => sectionContent.value.closing_text || 'Делая лучше хотя бы одному живому существу, мы оказываем большую помощь себе, и это не может не сказаться на качестве и скорости изменений в вашей жизни после Игры.',
)
const metrics = computed(() => {
  const source = Array.isArray(sectionContent.value.metrics) && sectionContent.value.metrics.length
    ? sectionContent.value.metrics
    : fallbackMetrics
  return source.map((metric, index) => ({
    id: `metric-${index}`,
    value: metric.value || '',
    label: metric.label || '',
    icon: metricIcons[index % metricIcons.length],
  }))
})
const metricValue = (metric) => metric.value

let observer

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
      threshold: 0.16,
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
    id="guide"
    ref="sectionRef"
    class="relative scroll-mt-24 overflow-hidden bg-[#F8F3EA] px-5 py-12 text-[#24231F] sm:px-6 md:px-8 md:py-16"
  >
    <div class="pointer-events-none absolute left-[-160px] top-[-160px] h-[360px] w-[360px] rounded-full bg-white/80 blur-3xl" />
    <div class="pointer-events-none absolute bottom-[-180px] right-[-140px] h-[420px] w-[420px] rounded-full bg-[#8B7449]/30 blur-3xl" />

    <div class="relative mx-auto max-w-[1120px]">
      <div class="mb-7 max-w-3xl">
        <span class="mb-3 inline-flex rounded-full border border-[#8B7449]/40 bg-white/70 px-4 py-2 text-[11px] font-medium uppercase tracking-[0.24em] text-[#8B7449]">
          {{ guideTag }}
        </span>

        <h2 class="text-3xl font-semibold leading-[1.04] tracking-[-0.04em] text-[#24231F] sm:text-4xl md:text-5xl">
          {{ guideTitle }}
          <span class="block text-[#8B7449]">{{ guideBrand }}</span>
        </h2>
      </div>

      <div class="grid gap-5 lg:grid-cols-[390px_1fr] lg:items-start">
        <div
          class="group relative h-[520px] overflow-hidden rounded-[1.75rem] bg-white p-2.5 shadow-[0_24px_70px_rgba(45,35,20,0.14)] transition-all duration-1000 ease-out sm:h-[560px] lg:h-[610px]"
          :class="isVisible ? 'translate-x-0 translate-y-0 opacity-100 blur-0' : '-translate-x-8 translate-y-8 opacity-0 blur-sm'"
        >
          <div class="relative h-full overflow-hidden rounded-[1.35rem]">
            <img
              :src="imageUrl"
              :alt="imageAlt"
              class="h-full w-full object-cover object-center transition duration-700 group-hover:scale-[1.03]"
              loading="lazy"
              decoding="async"
            >

            <div class="absolute inset-0 bg-black/20" />

            <div class="absolute bottom-4 left-4 right-4 rounded-2xl border border-white/20 bg-white/18 p-4 text-white shadow-2xl backdrop-blur-xl">
              <p class="text-[11px] uppercase tracking-[0.24em] text-white/70">
                {{ guideBrand }}
              </p>

              <p class="mt-2 text-lg font-semibold leading-tight sm:text-xl">
                {{ guideCaption }}
              </p>
            </div>
          </div>
        </div>

        <div
          class="rounded-[1.75rem] border border-white/70 bg-white/80 p-5 shadow-[0_22px_65px_rgba(45,35,20,0.09)] backdrop-blur-xl transition-all delay-150 duration-1000 ease-out sm:p-6 lg:h-[610px] lg:overflow-hidden"
          :class="isVisible ? 'translate-x-0 translate-y-0 opacity-100 blur-0' : 'translate-x-8 translate-y-8 opacity-0 blur-sm'"
        >
          <div class="guide-scroll lg:h-full lg:overflow-y-auto lg:pr-3">
            <div class="space-y-4 text-[14px] leading-7 text-stone-700 sm:text-[15px]">
              <p
                v-for="paragraph in introParagraphs"
                :key="paragraph"
              >
                {{ paragraph }}
              </p>
            </div>

            <div class="mt-6 space-y-4 text-[14px] leading-7 text-stone-700 sm:text-[15px]">
              <p
                v-for="paragraph in expandedParagraphs"
                :key="paragraph"
              >
                {{ paragraph }}
              </p>
            </div>

            <div class="my-6 rounded-[1.35rem] border border-[#8B7449]/50 bg-[#FBF7EF] p-5">
              <p class="text-[12px] font-medium uppercase tracking-[0.18em] text-[#8B7449]">
                {{ resultsTitle }}
              </p>

              <ul class="mt-4 grid gap-2.5">
                <li
                  v-for="item in results"
                  :key="item"
                  class="flex gap-3 text-[14px] leading-6 text-stone-700"
                >
                  <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#8B7449]" />
                  <span>{{ item }}</span>
                </li>
              </ul>
            </div>

            <div class="space-y-4 text-[14px] leading-7 text-stone-700 sm:text-[15px]">
              <p
                v-for="paragraph in finalParagraphs"
                :key="paragraph"
              >
                {{ paragraph }}
              </p>
            </div>

            <div class="mt-6 rounded-[1.35rem] border border-[#8B7449]/25 bg-[#FBF7EF] p-5 shadow-inner shadow-white/40">
              <div class="flex gap-4">
                <span class="mt-1 h-10 w-1 shrink-0 rounded-full bg-[#8B7449]" />
                <p class="text-[16px] font-medium leading-7 text-[#24231F] sm:text-[17px] sm:leading-8">
                  {{ closingText }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article
          v-for="(metric, index) in metrics"
          :key="metric.id"
          class="group relative min-h-[118px] overflow-hidden rounded-[1.35rem] border border-white/75 bg-white p-4 shadow-[0_16px_45px_rgba(45,35,20,0.08)] transition-all duration-700 ease-out hover:-translate-y-1 hover:shadow-[0_22px_55px_rgba(45,35,20,0.13)]"
          :class="isVisible ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'"
          :style="{ transitionDelay: `${320 + index * 110}ms` }"
        >
          <div class="pointer-events-none absolute -right-8 -top-8 h-20 w-20 rounded-full bg-[#8B7449]" />

          <span class="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-[#24231F] text-white shadow-lg shadow-[#24231F]/20 transition duration-300 group-hover:scale-105 group-hover:bg-[#8B7449]">
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path :d="metric.icon" />
            </svg>
          </span>

          <div class="relative mt-4">
            <span class="block text-2xl font-semibold leading-none tracking-[-0.035em] text-[#24231F]">
              {{ metricValue(metric) }}
            </span>

            <span class="mt-1.5 block max-w-[180px] text-xs font-medium leading-5 text-stone-600">
              {{ metric.label }}
            </span>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.guide-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(159, 133, 84, 0.45) transparent;
}

.guide-scroll::-webkit-scrollbar {
  width: 6px;
}

.guide-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.guide-scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(159, 133, 84, 0.42);
}
</style>
