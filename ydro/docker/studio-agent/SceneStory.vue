<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  chapters: { type: Array, required: true },
  mode: { type: String, default: 'split' },
  label: { type: String, default: 'История' },
})

const items = computed(() => props.chapters.slice(0, 8))
const variant = computed(() => ['split', 'overlay', 'reverse'].includes(props.mode) ? props.mode : 'split')
const root = ref(null)
const active = ref(0)
let raf = 0
let observer

function update() {
  raf = 0
  if (!root.value) return
  const chapters = Array.from(root.value.querySelectorAll('[data-tn-story-chapter]'))
  if (!chapters.length) return

  const focusLine = window.innerHeight * 0.5
  let nearest = Infinity
  let index = 0
  chapters.forEach((chapter, i) => {
    const rect = chapter.getBoundingClientRect()
    const distance = Math.abs(rect.top + rect.height * 0.5 - focusLine)
    if (distance < nearest) {
      nearest = distance
      index = i
    }
  })
  active.value = index
}

function schedule() {
  if (!raf) raf = requestAnimationFrame(update)
}

onMounted(() => {
  window.addEventListener('scroll', schedule, { passive: true })
  window.addEventListener('resize', schedule, { passive: true })
  observer = new ResizeObserver(schedule)
  observer.observe(root.value)
  schedule()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', schedule)
  window.removeEventListener('resize', schedule)
  observer?.disconnect()
  cancelAnimationFrame(raf)
})
</script>

<template>
  <div
    ref="root"
    class="tn-story"
    :class="'tn-story--' + variant"
    data-tn-story
    :data-tn-active="active"
    data-tn-camera-track
    role="region"
    :aria-label="label"
  >
    <div class="tn-story-stage" aria-hidden="true">
      <div class="tn-story-visual">
        <slot name="visual" :item="items[active]" :index="active">
          <img v-if="items[active]?.image" :src="items[active].image" alt="" loading="lazy">
        </slot>
      </div>
      <span class="tn-story-counter">{{ String(active + 1).padStart(2, '0') }} / {{ String(items.length).padStart(2, '0') }}</span>
    </div>

    <div class="tn-story-chapters">
      <article
        v-for="(item, index) in items"
        :key="index"
        class="tn-story-chapter"
        data-tn-story-chapter
        :data-active="index === active"
      >
        <div class="tn-story-mobile-visual" aria-hidden="true">
          <slot name="mobile-visual" :item="item" :index="index">
            <img v-if="item.image" :src="item.image" alt="" loading="lazy">
          </slot>
        </div>

        <div class="tn-story-caption">
          <slot name="chapter" :item="item" :index="index" :active="index === active">
            <p v-if="item.kicker" class="tn-story-kicker">{{ item.kicker }}</p>
            <h3>{{ item.title }}</h3>
            <p>{{ item.text }}</p>
            <img v-if="item.image" class="tn-story-inline-image" :src="item.image" :alt="item.alt || ''" loading="lazy">
          </slot>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.tn-story {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, .92fr);
  gap: clamp(28px, 5vw, 88px);
  position: relative;
  min-width: 0;
  isolation: isolate;
}

.tn-story-stage {
  position: sticky;
  top: var(--tn-story-top, 100px);
  height: min(66vh, 680px);
  min-height: 420px;
  align-self: start;
  min-width: 0;
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
}

.tn-story-visual {
  position: relative;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  border-radius: var(--tn-story-radius, 2px);
  background: var(--tn-story-bg, #eee6da);
}

.tn-story-visual > img,
.tn-story-mobile-visual > img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tn-story-counter,
.tn-story-kicker {
  font-size: .76rem;
  letter-spacing: .15em;
  font-variant-numeric: tabular-nums;
}

.tn-story-counter { padding: 12px 0; }
.tn-story-chapters { min-width: 0; }
.tn-story-chapter {
  min-height: min(62vh, 620px);
  display: flex;
  align-items: center;
  min-width: 0;
}

.tn-story-caption {
  max-width: 56ch;
  padding: 24px 0;
  opacity: .36;
  transition: opacity .45s ease, transform .45s ease;
  transform: translateY(12px);
}
.tn-story-chapter[data-active='true'] .tn-story-caption {
  opacity: 1;
  transform: translateY(0);
}
.tn-story-caption h3 {
  font-size: clamp(1.9rem, 4.5vw, 4.2rem);
  line-height: 1.02;
  letter-spacing: -.045em;
  margin: .35em 0;
}
.tn-story-caption p { line-height: 1.7; margin: .5em 0; }
.tn-story-inline-image { display: none; width: 100%; height: auto; margin: 20px 0 0; }
.tn-story-mobile-visual { display: none; }

.tn-story--reverse { grid-template-columns: minmax(0, .92fr) minmax(0, 1.08fr); }
.tn-story--reverse .tn-story-stage { grid-column: 2; grid-row: 1; }
.tn-story--reverse .tn-story-chapters { grid-column: 1; grid-row: 1; }
.tn-story--overlay { grid-template-columns: minmax(0, 1fr); gap: 0; }
.tn-story--overlay .tn-story-stage,
.tn-story--overlay .tn-story-chapters { grid-column: 1; grid-row: 1; }
.tn-story--overlay .tn-story-stage { height: min(82vh, 860px); }
.tn-story--overlay .tn-story-chapters {
  position: relative;
  z-index: 1;
  pointer-events: none;
  padding: 0 clamp(16px, 4vw, 64px);
}
.tn-story--overlay .tn-story-caption {
  padding: clamp(16px, 3vw, 32px);
  color: var(--tn-caption-color, #fff);
  background: var(--tn-caption-bg, rgba(15, 17, 22, .86));
  pointer-events: auto;
}

@media (max-width: 760px), (prefers-reduced-motion: reduce) {
  .tn-story,
  .tn-story--reverse,
  .tn-story--overlay { display: block; }
  .tn-story .tn-story-stage { display: none; }
  .tn-story .tn-story-chapters { padding: 0; pointer-events: auto; }
  .tn-story .tn-story-chapter {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
    min-height: 0;
    padding: clamp(24px, 6vw, 40px) 0;
    border-bottom: 1px solid rgba(80, 65, 46, .14);
  }
  .tn-story .tn-story-mobile-visual {
    display: block;
    width: 100%;
    min-width: 0;
    min-height: 0;
    overflow: visible;
  }
  .tn-story .tn-story-caption {
    opacity: 1;
    transform: none;
    transition: none;
    max-width: none;
    padding: 0;
  }
  .tn-story-inline-image { display: block; }
}
</style>