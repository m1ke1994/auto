<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const props = defineProps({
  items: { type: Array, default: () => [] },
  label: { type: String, default: 'Key facts' },
  once: { type: Boolean, default: true },
  duration: { type: Number, default: 1.65 },
})

const root = ref(null)
const cards = ref([])
const state = ref('idle')
const tweens = []
let trigger
let media

function parseMetric(item, index) {
  const source = String(item?.value ?? '').trim()
  const match = source.match(/[-+]?\d+(?:[.,]\d+)?/)
  if (!match) return null
  const rawNumber = match[0].replace(',', '.')
  const target = Number(rawNumber)
  if (!Number.isFinite(target)) return null
  const inferredDecimals = rawNumber.includes('.') ? rawNumber.split('.')[1].length : 0
  const decimals = Math.max(0, Math.min(4, Number.isInteger(item?.decimals) ? item.decimals : inferredDecimals))
  const start = match.index ?? 0
  return reactive({
    id: item?.id ?? `metric-${index}`,
    label: String(item?.label ?? '').trim(),
    prefix: String(item?.prefix ?? '') + source.slice(0, start),
    suffix: source.slice(start + match[0].length) + String(item?.suffix ?? ''),
    target,
    decimals,
    current: 0,
  })
}

const metrics = computed(() => props.items.map(parseMetric).filter(Boolean))
const numericText = metric => `${metric.current < 0 ? '-' : ''}${Math.abs(metric.current).toFixed(metric.decimals)}`
const finalText = metric => `${metric.prefix}${metric.target < 0 ? '-' : ''}${Math.abs(metric.target).toFixed(metric.decimals)}${metric.suffix}`
const characters = metric => `${metric.prefix}${numericText(metric)}${metric.suffix}`.split('')
const digitStyle = character => ({ transform: `translate3d(0, -${Number(character)}em, 0)` })

function finish() {
  metrics.value.forEach(metric => { metric.current = metric.target })
  state.value = 'complete'
  gsap.set(cards.value, { autoAlpha: 1, y: 0 })
}

function play() {
  if (state.value === 'running' || (props.once && state.value === 'complete')) return
  state.value = 'running'
  gsap.to(cards.value, { autoAlpha: 1, y: 0, duration: .7, stagger: .09, ease: 'power3.out' })
  metrics.value.forEach((metric, index) => {
    metric.current = 0
    const proxy = { value: 0 }
    tweens.push(gsap.to(proxy, {
      value: metric.target,
      duration: Math.max(.2, props.duration + index * .08),
      ease: 'power3.out',
      onUpdate: () => { metric.current = proxy.value },
      onComplete: () => {
        metric.current = metric.target
        if (index === metrics.value.length - 1) state.value = 'complete'
      },
    }))
  })
}

onMounted(async () => {
  await nextTick()
  if (!root.value || !metrics.value.length) return
  media = window.matchMedia('(prefers-reduced-motion: reduce)')
  if (media.matches) { finish(); return }
  gsap.set(cards.value, { autoAlpha: 0, y: 24 })
  trigger = ScrollTrigger.create({
    trigger: root.value,
    start: 'top 82%',
    once: props.once,
    onEnter: play,
    onEnterBack: () => { if (!props.once) play() },
  })
})

onBeforeUnmount(() => {
  trigger?.kill()
  tweens.splice(0).forEach(tween => tween.kill())
})
</script>

<template>
  <section
    v-if="metrics.length"
    ref="root"
    class="tn-about-metrics"
    :aria-label="label"
    :data-tn-metric-state="state"
    data-tn-about-metrics
  >
    <article
      v-for="(metric, index) in metrics"
      :key="metric.id"
      :ref="element => { if (element) cards[index] = element }"
      class="tn-about-metric"
      :data-tn-metric-value="finalText(metric)"
      data-tn-metric
    >
      <span class="tn-metric-screenreader">{{ finalText(metric) }} {{ metric.label }}</span>
      <span class="tn-metric-value" aria-hidden="true">
        <template v-for="(character, characterIndex) in characters(metric)" :key="characterIndex">
          <span v-if="/\d/.test(character)" class="tn-metric-digit-window">
            <span class="tn-metric-digit-track" :style="digitStyle(character)">
              <span v-for="digit in 10" :key="digit">{{ digit - 1 }}</span>
            </span>
          </span>
          <span v-else class="tn-metric-symbol">{{ character }}</span>
        </template>
      </span>
      <span v-if="metric.label" class="tn-metric-label">{{ metric.label }}</span>
    </article>
  </section>
</template>

<style scoped>
.tn-about-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,13rem),1fr));gap:clamp(.8rem,2vw,1.4rem);width:100%}
.tn-about-metric{min-width:0;padding:clamp(1.25rem,3vw,2.1rem);border:1px solid color-mix(in srgb,currentColor 16%,transparent);border-radius:clamp(1rem,2vw,1.75rem);background:color-mix(in srgb,currentColor 4%,transparent);contain:layout paint}
.tn-metric-value{display:flex;align-items:baseline;min-height:1em;font-weight:600;font-size:clamp(2.5rem,7vw,5.75rem);line-height:1;font-family:var(--tn-metric-font,ui-sans-serif,system-ui,sans-serif);letter-spacing:-.055em;font-variant-numeric:tabular-nums}
.tn-metric-digit-window{display:inline-block;width:.61em;height:1em;overflow:hidden;vertical-align:bottom}
.tn-metric-digit-track{display:block;will-change:transform;transition:transform 90ms cubic-bezier(.2,.7,.2,1)}
.tn-metric-digit-track>span{display:block;width:.61em;height:1em;line-height:1;text-align:center}
.tn-metric-symbol{display:inline-block;white-space:pre}
.tn-metric-label{display:block;max-width:22rem;margin-top:clamp(.75rem,1.5vw,1.1rem);font-size:clamp(.78rem,1.3vw,.95rem);line-height:1.45;letter-spacing:.07em;text-transform:uppercase;opacity:.68}
.tn-metric-screenreader{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:560px){.tn-about-metrics{grid-template-columns:1fr 1fr}.tn-about-metric{padding:1.1rem}.tn-metric-value{font-size:clamp(2.15rem,13vw,3.5rem)}}
@media(max-width:380px){.tn-about-metrics{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.tn-about-metric{opacity:1!important;transform:none!important}.tn-metric-digit-track{transition:none!important}}
</style>
