<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import ModularCube from './ModularCube.vue'
import { clamp, smoothRange } from './storyMotion.js'
import {
  filmScenes as scenes,
  filmSceneAt,
  filmCubeAt,
  filmSceneStyle,
} from './filmTimeline.js'
const props = defineProps({ services: { type: Array, required: true } })
const reel = ref(null)
const stage = ref(null)
const progress = ref(0)
const reduced = ref(false)
const shot = computed(() => filmSceneAt(progress.value))
const activeService = computed(() =>
  shot.value >= 2 && shot.value <= 5 ? shot.value - 2 : -1,
)
const narratives = [
  {
    lines: ['За каждым', 'действием —', 'свой след.'],
    description:
      'Откуда пришёл посетитель. Какие страницы посмотрел. Что сделал дальше. Аналитика TrackNode помогает увидеть путь человека на сайте.',
    detail: 'Посещения · Источники · Страницы · События',
    thought: 'Увидеть то, что обычно остаётся за кадром.',
  },
  {
    lines: ['Обращение.', 'Контекст.', 'Следующий шаг.'],
    description:
      'Имя, контакты, комментарий и страница обращения — в одной заявке. Статус помогает видеть, что новое, что в работе и что уже завершено.',
    detail: 'Новая · В работе · Завершена',
    thought: 'Дать каждому обращению своё место.',
  },
  {
    lines: ['Замечать', 'то, что', 'мешает.'],
    description:
      'Техническая проверка показывает найденные проблемы сайта. Критичные ошибки, важные замечания и рекомендации помогают определить, с чего начать.',
    detail: 'Проверка · Проблемы · Приоритеты',
    thought: 'Сначала увидеть проблему. Затем выбрать действие.',
  },
  {
    lines: ['История', 'не заканчивается', 'запуском.'],
    description:
      'Разделы сайта можно открывать и редактировать в кабинете TrackNode. Меняйте доступные заголовки, описания и другие поля по мере развития проекта.',
    detail: 'Разделы · Тексты · Изменения',
    thought: 'Содержание меняется вместе с вашим делом.',
  },
]
const take = computed(() =>
  activeService.value < 0
    ? 0
    : clamp(
        (progress.value - scenes[shot.value].start) /
          (scenes[shot.value].end - scenes[shot.value].start),
      ),
)
const cubeProgress = computed(() => filmCubeAt(progress.value))
const serviceWeight = computed(
  () =>
    smoothRange(progress.value, 0.23, 0.27) *
    (1 - smoothRange(progress.value, 0.735, 0.78)),
)
const objectStyle = computed(() => ({
  transform: `translate3d(${22 * (1 - smoothRange(progress.value, 0.06, 0.18)) + 17 * serviceWeight.value}%,${3 * serviceWeight.value}%,0) scale(${1 + 0.07 * serviceWeight.value})`,
  opacity:
    1 -
    0.12 * serviceWeight.value -
    0.65 * smoothRange(progress.value, 0.87, 0.98),
}))
function style(index) {
  return filmSceneStyle(index, progress.value)
}
let frame = 0,
  visible = false,
  observer,
  resizeObserver,
  media,
  lastUpdate = 0
function update(now) {
  frame = 0
  if (!reel.value || !visible || document.hidden) return
  const rect = reel.value.getBoundingClientRect()
  const target = clamp(-rect.top / Math.max(1, rect.height - (stage.value?.clientHeight || window.innerHeight)))
  const dt = Math.min((now - (lastUpdate || now - 16.7)) / 1000, 0.05)
  lastUpdate = now
  const delta = target - progress.value
  progress.value = reduced.value || Math.abs(delta) < 0.00001
    ? target
    : progress.value + delta * (1 - Math.exp(-dt * 16))
  if (Math.abs(target - progress.value) >= 0.00001) schedule()
}
function schedule() {
  if (!frame && visible && !document.hidden)
    frame = requestAnimationFrame(update)
}
function visibility() {
  if (document.hidden) {
    cancelAnimationFrame(frame)
    frame = 0
  } else schedule()
}
function hashNavigation() {
  if (!reduced.value) return
  const targets = {
    top: 0,
    system: 1,
    features: 2,
    analytics: 2,
    website: 6,
    pwa: 6,
    pricing: 7,
  }
  const target = targets[window.location.hash.slice(1)]
  if (target !== undefined) go(target)
}
function changeMotion() {
  reduced.value = media.matches
  schedule()
}
function go(index) {
  if (reduced.value) {
    reel.value.querySelector(`[data-shot="${index}"]`)?.scrollIntoView()
    return
  }
  const rect = reel.value.getBoundingClientRect()
  const mark = index === 0 ? 0 : scenes[index].start + 0.035
  window.scrollTo({
    top: window.scrollY + rect.top + mark * (rect.height - (stage.value?.clientHeight || window.innerHeight)),
    behavior: 'smooth',
  })
}
function anchor(position) {
  return { top: `calc(${position * 100}% - ${position * 100}svh)` }
}
onMounted(() => {
  media = matchMedia('(prefers-reduced-motion: reduce)')
  changeMotion()
  media.addEventListener('change', changeMotion)
  window.addEventListener('hashchange', hashNavigation)
  observer = new IntersectionObserver(
    ([entry]) => {
      visible = entry.isIntersecting
      if (visible) schedule()
      else {
        cancelAnimationFrame(frame)
        frame = 0
      }
    },
    { rootMargin: '150px' },
  )
  observer.observe(reel.value)
  resizeObserver = new ResizeObserver(schedule)
  resizeObserver.observe(reel.value)
  window.addEventListener('scroll', schedule, { passive: true })
  window.addEventListener('resize', schedule, { passive: true })
  document.addEventListener('visibilitychange', visibility)
})
onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  observer?.disconnect()
  resizeObserver?.disconnect()
  window.removeEventListener('scroll', schedule)
  window.removeEventListener('resize', schedule)
  document.removeEventListener('visibilitychange', visibility)
  media?.removeEventListener('change', changeMotion)
  window.removeEventListener('hashchange', hashNavigation)
})
</script>
<template>
  <div
    id="top"
    ref="reel"
    class="film-reel"
    :class="{ 'motion-reduced': reduced }"
  >
    <span id="system" class="film-anchor" :style="anchor(0.16)"></span
    ><span id="features" class="film-anchor" :style="anchor(0.285)"></span
    ><span id="analytics" class="film-anchor" :style="anchor(0.285)"></span
    ><span id="website" class="film-anchor" :style="anchor(0.79)"></span
    ><span id="pwa" class="film-anchor" :style="anchor(0.79)"></span
    ><span id="pricing" class="film-anchor" :style="anchor(0.92)"></span>
    <div ref="stage" class="film-stage">
      <div
        class="film-light"
        aria-hidden="true"
        :style="{
          transform: `translate3d(${progress * 18}%,${progress * -12}%,0)`,
        }"
      ></div>
      <div class="film-object" :style="objectStyle">
        <ModularCube
          cinematic
          portrait
          :take="take"
          :progress="reduced ? 1 : cubeProgress"
          :active="activeService"
          :services="[]"
        />
      </div>
      <div class="film-grain" aria-hidden="true"></div>
      <div class="letterbox top" aria-hidden="true"></div>
      <div class="letterbox bottom" aria-hidden="true"></div>
      <div class="film-meta">
        <span>TRACKNODE — ВСЁ СВЯЗАНО</span><span>0{{ shot + 1 }} / 08</span>
      </div>
      <section
        data-shot="0"
        class="film-shot opening"
        :style="style(0)"
        :inert="!reduced && shot !== 0"
        :aria-hidden="!reduced && shot !== 0"
      >
        <div class="opening-copy">
          <p class="film-kicker">Новый взгляд на работу</p>
          <h1>Меньше хаоса.<br /><span>Больше контроля.</span></h1>
          <p class="film-description">
            Сайт, аналитика посетителей, заявки и SEO-аудит — в одной системе
            TrackNode.
          </p>
          <div class="film-actions">
            <RouterLink to="/register" class="film-button"
              >Начать работу <span>↗</span></RouterLink
            ><button class="film-link" @click="go(1)">
              Раскрыть систему <span>↓</span>
            </button>
          </div>
        </div>
        <div class="opening-aside">
          <span>Отдельные инструменты.<br />Общая картина.</span
          ><b aria-hidden="true">+</b>
        </div>
      </section>
      <section
        data-shot="1"
        class="film-shot fracture"
        :style="style(1)"
        :inert="!reduced && shot !== 1"
        :aria-hidden="!reduced && shot !== 1"
      >
        <p class="film-kicker">Действие I / Разобрать сложное</p>
        <h2>За целым —<br /><em>связанные детали.</em></h2>
        <p class="fracture-note">
          У каждого модуля — своя задача.<br />Вместе они показывают больше.
        </p>
        <span class="shot-word" aria-hidden="true">СВЯЗИ</span>
      </section>
      <section
        v-for="(service, index) in services"
        :key="service.title"
        :data-shot="index + 2"
        class="film-shot service-shot"
        :class="'service-shot-' + index"
        :style="style(index + 2)"
        :inert="!reduced && shot !== index + 2"
        :aria-hidden="!reduced && shot !== index + 2"
      >
        <div class="service-editorial">
          <p class="film-kicker">
            Действие II / 0{{ index + 1 }} — {{ service.title }}
          </p>
          <h2 class="narrative-heading">
            <span
              v-for="(line, lineIndex) in narratives[index].lines"
              :key="line"
              :class="{ accent: lineIndex === 2 }"
              >{{ line }}</span
            >
          </h2>
          <p class="film-description">{{ narratives[index].description }}</p>
          <div class="narrative-detail">
            <span class="detail-rule"></span>{{ narratives[index].detail }}
          </div>
        </div>
        <div class="object-annotation">
          <span class="annotation-line" aria-hidden="true"></span>
          <div>
            <span class="module-code">TN / 0{{ index + 1 }}</span>
            <h3>{{ service.title }}</h3>
            <p>{{ narratives[index].thought }}</p>
          </div>
        </div>
      </section>
      <section
        data-shot="6"
        class="film-shot synthesis"
        :style="style(6)"
        :inert="!reduced && shot !== 6"
        :aria-hidden="!reduced && shot !== 6"
      >
        <div>
          <p class="film-kicker">Действие III / Собрать главное</p>
          <h2>Работа.<br />В одной<br /><em>системе.</em></h2>
          <p class="film-description">
            Разрабатываем сайт под задачи бизнеса. После запуска — данные,
            обращения и работа с содержанием в кабинете TrackNode.
          </p>
        </div>
        <div class="synthesis-caption">
          <span>Сайт → Данные → Решения</span>
          <p>TrackNode можно добавить<br />на главный экран смартфона.</p>
        </div>
      </section>
      <section
        data-shot="7"
        class="film-shot final-shot"
        :style="style(7)"
        :inert="!reduced && shot !== 7"
        :aria-hidden="!reduced && shot !== 7"
      >
        <p class="film-kicker">Продолжение — за вами</p>
        <h2>Соберите<br /><em>свою систему.</em></h2>
        <p class="film-description">
          Стоимость разработки рассчитывается индивидуально после обсуждения
          задач, структуры и функциональности. Разработка и дальнейшее развитие
          — по согласованному объёму.
        </p>
        <div class="film-actions">
          <RouterLink class="film-button" to="/register"
            >Начать работу <span>↗</span></RouterLink
          ><a class="film-link" href="#contact"
            >Обсудить проект <span>↓</span></a
          >
        </div>
        <RouterLink class="film-terms" to="/terms"
          >Условия использования сервиса</RouterLink
        >
      </section>
      <nav class="film-timeline" aria-label="Сцены лендинга">
        <span class="timeline-cue">Листайте — история продолжается</span>
        <div class="timeline-scenes">
          <button
            v-for="(scene, index) in scenes"
            :key="scene.name"
            :aria-label="'Сцена ' + (index + 1) + ': ' + scene.name"
            :aria-current="shot === index ? 'step' : undefined"
            @click="go(index)"
          >
            <span
              class="scene-fill"
              :style="{
                transform: `scaleX(${clamp((progress - scene.start) / (scene.end - scene.start))})`,
              }"
            ></span
            ><span class="scene-dot"></span>
          </button>
        </div>
        <a href="#contact">К разговору <span>↗</span></a>
      </nav>
    </div>
  </div>
</template>
<style scoped>
.film-reel {
  --ice: #8bb6ff;
  position: relative;
  height: 760svh;
  background: #080c12;
  color: #f1f4fa;
  isolation: isolate;
}
.film-anchor {
  position: absolute;
  left: 0;
  width: 1px;
  height: 1px;
  pointer-events: none;
}
.film-stage {
  position: sticky;
  top: 0;
  height: 100svh;
  min-height: 0;
  overflow: hidden;
  background:
    radial-gradient(ellipse at 76% 46%, #1b2a4180, transparent 62%), #0b0f16;
}
.film-object {
  position: absolute;
  inset: 0;
  will-change: transform, opacity;
  transform-origin: center;
  pointer-events: auto;
}
.film-light {
  position: absolute;
  inset: -20%;
  background: radial-gradient(ellipse at 60% 50%, #4d76b321, transparent 48%);
  pointer-events: none;
}
.film-grain {
  position: absolute;
  inset: 0;
  opacity: 0.035;
  pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Cpath fill='%23fff' filter='url(%23n)' opacity='.7' d='M0 0h180v180H0z'/%3E%3C/svg%3E");
}
.letterbox {
  position: absolute;
  left: 0;
  right: 0;
  height: 25px;
  background: #080b10;
  z-index: 3;
  pointer-events: none;
}
.letterbox.top {
  top: 0;
}
.letterbox.bottom {
  bottom: 0;
}
.film-meta {
  position: absolute;
  z-index: 5;
  left: 48px;
  right: 48px;
  top: 96px;
  display: flex;
  justify-content: space-between;
  color: #72849f;
  font-size: 8px;
  letter-spacing: 2px;
  pointer-events: none;
}
.film-shot {
  position: absolute;
  inset: 0;
  padding: 110px max(48px, calc((100vw - 1280px) / 2));
  display: flex;
  align-items: center;
  will-change: transform, opacity;
  transform-origin: center;
  pointer-events: none;
}
.film-shot a,
.film-shot button {
  pointer-events: auto;
}
.film-kicker {
  font-size: 9px;
  letter-spacing: 2.1px;
  text-transform: uppercase;
  color: #8ca9d3;
  margin: 0 0 30px;
}
.opening-copy {
  width: 58%;
  position: relative;
  z-index: 2;
}
.film-shot h1 {
  font-size: clamp(42px, 5.4vw, 80px);
  font-weight: 450;
  line-height: 1.07;
  letter-spacing: -3.8px;
  margin: 0;
  white-space: nowrap;
}
.film-shot h1 span {
  color: #9baac1;
}
.film-description {
  max-width: 405px;
  color: #9caac0;
  font-size: 14px;
  line-height: 1.85;
  margin: 28px 0;
}
.film-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 26px;
  margin-top: 30px;
}
.film-button {
  display: inline-flex;
  align-items: center;
  gap: 38px;
  min-height: 52px;
  padding: 0 23px;
  background: #386ff4;
  border: 1px solid #729eff;
  border-radius: 5px;
  font-size: 12px;
  color: #fff;
  text-decoration: none;
}
.film-button:hover {
  background: #5586fa;
}
.film-link {
  display: inline-flex;
  align-items: center;
  gap: 23px;
  border: 0;
  background: none;
  color: #c3d0e6;
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
  text-decoration: none;
  padding: 0;
}
.opening-aside {
  position: absolute;
  right: 8%;
  bottom: 22%;
  color: #657a9b;
  display: flex;
  gap: 70px;
  align-items: center;
  font-size: 11px;
  line-height: 1.8;
}
.opening-aside b {
  font-size: 40px;
  font-weight: 200;
}
.film-shot h2 {
  font-size: clamp(42px, 5.8vw, 85px);
  font-weight: 430;
  line-height: 1.03;
  letter-spacing: -3px;
  margin: 0;
}
.film-shot h2 em {
  font-style: normal;
  color: #9eb9e4;
}
.fracture {
  display: block;
  padding-top: 14%;
  text-align: center;
}
.fracture h2 {
  font-size: clamp(38px, 4.2vw, 62px);
  line-height: 1.1;
}
.fracture .film-kicker {
  margin-bottom: 23px;
}
.fracture-note {
  position: absolute;
  bottom: 19%;
  right: 8%;
  text-align: left;
  color: #97a9c4;
  font-size: 12px;
  line-height: 1.9;
}
.shot-word {
  position: absolute;
  left: 5%;
  bottom: 13%;
  font-size: clamp(80px, 18vw, 240px);
  letter-spacing: -12px;
  color: #b5d1ff06;
  font-weight: 600;
  line-height: 1;
  z-index: -1;
}
.service-shot {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}
.service-editorial {
  position: relative;
  z-index: 2;
  width: 51%;
  max-width: 640px;
}
.narrative-heading {
  font-size: clamp(44px, 4.9vw, 72px) !important;
  line-height: 1.02 !important;
  letter-spacing: -2.7px !important;
}
.narrative-heading > span {
  display: block;
}
.narrative-heading .accent {
  color: #9bbce9;
}
.service-editorial .film-description {
  max-width: 395px;
  color: #9aaecb;
  font-size: 13px;
  line-height: 1.9;
  margin: 28px 0 0;
}
.narrative-detail {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 32px;
  color: #5f7fa9;
  font-size: 9px;
  letter-spacing: 0.45px;
  line-height: 1.7;
}
.detail-rule {
  height: 1px;
  width: 26px;
  background: #6a91c7;
  flex: none;
}
.object-annotation {
  position: absolute;
  right: 8%;
  bottom: 18%;
  max-width: 300px;
  display: flex;
  gap: 22px;
  align-items: flex-start;
}
.annotation-line {
  width: 45px;
  height: 1px;
  background: #90b7ed70;
  margin-top: 9px;
  position: relative;
}
.annotation-line:before {
  content: '';
  width: 4px;
  height: 4px;
  background: #8eb6ef;
  position: absolute;
  left: 0;
  top: -1px;
  border-radius: 50%;
}
.module-code {
  color: #5d7b9f;
  font: 8px monospace;
  letter-spacing: 1.8px;
}
.object-annotation h3 {
  font-size: 18px;
  letter-spacing: -0.4px;
  color: #c5d9f4;
  font-weight: 450;
  margin: 9px 0;
}
.object-annotation p {
  font-size: 10px;
  line-height: 1.8;
  max-width: 200px;
  color: #748cac;
  margin: 0;
}
.service-shot-1 .narrative-heading .accent {
  color: #9cceee;
}
.service-shot-2 .narrative-heading .accent {
  color: #bec8d8;
}
.service-shot-3 .narrative-heading .accent {
  color: #88b5ff;
}
.synthesis > div:first-child {
  z-index: 2;
}
.synthesis h2 {
  font-size: clamp(65px, 7.7vw, 112px);
}
.synthesis .film-description {
  max-width: 330px;
  font-size: 12px;
}
.synthesis-caption {
  position: absolute;
  right: 8%;
  bottom: 21%;
  color: #91a5c6;
  font-size: 11px;
  line-height: 1.8;
}
.synthesis-caption > span {
  color: #bdceea;
  font-size: 13px;
}
.synthesis-caption p {
  margin-top: 24px;
  color: #657e9e;
  font-size: 10px;
}
.final-shot {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.final-shot h2 {
  font-size: clamp(54px, 7.5vw, 110px);
  line-height: 1.05;
}
.final-shot .film-description {
  max-width: 510px;
  font-size: 12px;
  margin: 25px 0 0;
}
.final-shot .film-actions {
  justify-content: center;
}
.film-terms {
  margin-top: 25px;
  font-size: 10px;
  color: #748caf;
  text-decoration: none;
}
.film-timeline {
  position: absolute;
  left: 48px;
  right: 48px;
  bottom: 45px;
  z-index: 6;
  display: flex;
  align-items: center;
  gap: 40px;
  color: #6b809f;
  font-size: 9px;
}
.timeline-cue {
  white-space: nowrap;
}
.timeline-scenes {
  display: flex;
  gap: 7px;
  flex: 1;
  align-items: center;
}
.timeline-scenes button {
  position: relative;
  flex: 1;
  height: 26px;
  border: 0;
  background: none;
  cursor: pointer;
  padding: 0;
}
.timeline-scenes button:before {
  content: '';
  height: 1px;
  background: #677e9f44;
  position: absolute;
  left: 0;
  right: 0;
  top: 13px;
}
.scene-fill {
  position: absolute;
  height: 1px;
  inset: 13px 0 auto;
  background: #769ff1;
  transform-origin: left;
}
.scene-dot {
  position: absolute;
  left: 0;
  top: 11px;
  width: 5px;
  height: 5px;
  background: #91b5f6;
  border-radius: 50%;
  opacity: 0;
}
.timeline-scenes button[aria-current] .scene-dot {
  opacity: 1;
}
.film-timeline > a {
  display: flex;
  gap: 20px;
  text-decoration: none;
  color: #9db4d6;
  white-space: nowrap;
}
.film-shot :focus-visible,
.film-timeline :focus-visible {
  outline: 2px solid #9ec1ff;
  outline-offset: 6px;
}
@media (max-width: 1100px) {
  .film-shot {
    padding-inline: 28px;
    gap: 25px;
  }
  .film-meta,
  .film-timeline {
    left: 28px;
    right: 28px;
  }
  .service-editorial {
    width: 39%;
  }

  .opening-copy {
    width: 61%;
  }
  .film-shot h1 {
    font-size: clamp(41px, 5.4vw, 62px);
    letter-spacing: -2.5px;
  }
  .timeline-cue {
    display: none;
  }
  .film-timeline {
    gap: 25px;
  }

  .synthesis h2 {
    font-size: 80px;
  }
}
@media (max-width: 767px) {
  .film-reel {
    height: 690svh;
  }
  .film-meta {
    top: 90px;
    left: 20px;
    right: 20px;
    font-size: 7px;
    letter-spacing: 1.4px;
  }
  .letterbox {
    height: 12px;
  }
  .film-shot {
    padding: 85px 20px 90px;
    align-items: flex-start;
  }
  .opening-copy {
    width: 100%;
    margin-top: 44px;
  }
  .film-shot h1 {
    font-size: clamp(34px, 8.8vw, 58px);
    letter-spacing: -1.8px;
    line-height: 1.12;
    white-space: normal;
  }
  .film-kicker {
    font-size: 8px;
    letter-spacing: 1.6px;
    margin-bottom: 22px;
  }
  .film-description {
    font-size: 12px;
    line-height: 1.8;
    max-width: 340px;
    margin: 22px 0;
  }
  .film-actions {
    gap: 19px;
    margin-top: 23px;
  }
  .film-button {
    font-size: 11px;
    gap: 22px;
    min-height: 46px;
    padding-inline: 18px;
  }
  .film-link {
    font-size: 10px;
    gap: 14px;
  }
  .opening-aside {
    right: 24px;
    bottom: 19%;
    font-size: 9px;
    gap: 28px;
  }
  .opening-aside b {
    font-size: 30px;
  }
  .film-object {
    inset: 25% -30% 1% -30%;
  }
  .fracture {
    padding-top: 95px;
    text-align: left;
  }
  .film-shot h2 {
    font-size: 40px;
    letter-spacing: -1.7px;
    line-height: 1.1;
  }
  .fracture h2 {
    font-size: 37px;
    line-height: 1.13;
  }
  .fracture-note {
    right: 24px;
    bottom: 20%;
    font-size: 10px;
  }
  .shot-word {
    font-size: 100px;
    letter-spacing: -6px;
    bottom: 14%;
    left: 15px;
  }
  .service-shot {
    display: block;
    padding-top: 125px;
  }
  .service-editorial {
    width: 100%;
    max-width: none;
  }
  .service-editorial .film-kicker {
    margin-bottom: 18px;
    font-size: 7px;
  }

  .service-editorial .film-description {
    font-size: 10px;
    line-height: 1.7;
    margin-top: 13px;
    max-width: 95%;
  }

  .synthesis h2 {
    font-size: 67px;
  }
  .synthesis .film-description {
    font-size: 11px;
    max-width: 270px;
    margin-top: 24px;
  }
  .synthesis-caption {
    right: 22px;
    bottom: 18%;
    font-size: 9px;
  }
  .synthesis-caption > span {
    font-size: 10px;
  }
  .synthesis-caption p {
    font-size: 9px;
  }
  .final-shot {
    justify-content: center;
    padding-top: 75px;
  }
  .final-shot h2 {
    font-size: 47px;
    letter-spacing: -2px;
  }
  .final-shot .film-description {
    font-size: 11px;
    margin-top: 24px;
    max-width: 330px;
  }
  .final-shot .film-actions {
    gap: 18px;
  }
  .film-terms {
    font-size: 9px;
  }
  .film-timeline {
    left: 20px;
    right: 20px;
    bottom: 24px;
    gap: 18px;
  }
  .film-timeline > a {
    font-size: 9px;
    gap: 9px;
  }
  .timeline-scenes {
    gap: 5px;
  }
}
@media (max-height: 690px) and (min-width: 768px) {
  .film-shot {
    padding-block: 85px;
  }
  .film-shot h1 {
    font-size: 52px;
  }
  .film-description {
    font-size: 12px;
    margin-block: 20px;
  }

  .synthesis h2 {
    font-size: 70px;
  }
  .final-shot h2 {
    font-size: 75px;
  }
  .film-timeline {
    bottom: 32px;
  }
}
@media (max-height: 700px) and (max-width: 767px) {
  .opening-copy {
    margin-top: 25px;
  }
  .film-description {
    font-size: 11px;
    max-width: 300px;
  }
  .service-shot {
    padding-top: 112px;
  }
  .service-editorial .film-kicker {
    margin-bottom: 12px;
  }

  .service-editorial .film-description {
    font-size: 9px;
    margin-top: 9px;
  }

  .final-shot h2 {
    font-size: 42px;
  }
  .final-shot .film-description {
    font-size: 10px;
  }
  .synthesis h2 {
    font-size: 56px;
  }
  .synthesis .film-description {
    max-width: 240px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .film-reel {
    height: auto;
  }
  .film-stage {
    position: relative;
    height: auto;
    overflow: visible;
  }
  .film-object,
  .film-light,
  .film-grain,
  .letterbox,
  .film-meta,
  .film-anchor,
  .film-timeline,
  .opening-aside,
  .shot-word,
  .film-shot {
    position: relative;
    inset: auto;
    opacity: 1 !important;
    transform: none !important;
    visibility: visible !important;
    min-height: 580px;
    padding: 80px 48px;
    pointer-events: auto;
    border-bottom: 1px solid #ffffff15;
  }
  .opening-copy {
    width: 100%;
  }
  .film-shot h1 {
    white-space: normal;
  }
  .fracture {
    padding-top: 80px;
    text-align: left;
    min-height: 380px;
  }
  .fracture-note {
    position: static;
    margin-top: 40px;
  }
  .synthesis-caption {
    position: static;
    align-self: end;
    margin-left: auto;
  }

  .final-shot {
    min-height: 580px;
  }
  .film-kicker {
    margin-bottom: 25px;
  }
}
@media (prefers-reduced-motion: reduce) and (max-width: 767px) {
  .film-shot {
    padding: 60px 20px;
    min-height: 0;
  }
  .service-shot {
    display: block;
  }

  .synthesis {
    display: block;
  }
  .synthesis-caption {
    margin-top: 40px;
  }
  .final-shot {
    align-items: flex-start;
    text-align: left;
  }
  .final-shot .film-actions {
    justify-content: start;
  }
}

@media (max-width: 1100px) {
  .service-editorial {
    width: 55%;
    max-width: 510px;
  }
  .narrative-heading {
    font-size: 50px !important;
  }
  .service-editorial .film-description {
    max-width: 335px;
    font-size: 12px;
  }
  .object-annotation {
    right: 5%;
    bottom: 17%;
    gap: 15px;
  }
}
@media (max-width: 767px) {
  .service-shot {
    display: block;
    padding: 125px 20px 85px;
  }
  .service-editorial {
    width: 100%;
    max-width: none;
  }
  .narrative-heading {
    font-size: clamp(34px, 8.6vw, 49px) !important;
    letter-spacing: -1.4px !important;
    line-height: 1.06 !important;
  }
  .service-editorial .film-description {
    font-size: 11px;
    line-height: 1.8;
    max-width: 290px;
    margin-top: 20px;
  }
  .narrative-detail {
    font-size: 8px;
    margin-top: 20px;
    gap: 11px;
    max-width: 300px;
  }
  .object-annotation {
    right: 20px;
    bottom: 15%;
    max-width: 210px;
    gap: 12px;
  }
  .annotation-line {
    width: 26px;
  }
  .object-annotation h3 {
    font-size: 16px;
    margin-block: 7px;
  }
  .object-annotation p {
    font-size: 9px;
    max-width: 170px;
  }
  .film-object {
    inset: 30% -25% -2% -25%;
  }
}
@media (max-height: 700px) and (max-width: 767px) {
  .service-shot {
    padding-top: 112px;
  }
  .narrative-heading {
    font-size: 32px !important;
  }
  .service-editorial .film-description {
    font-size: 10px;
    max-width: 285px;
    line-height: 1.75;
    margin-top: 16px;
  }
  .narrative-detail {
    margin-top: 15px;
    font-size: 7px;
  }
  .object-annotation {
    bottom: 14%;
  }
  .object-annotation p {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .service-editorial {
    width: 100%;
    max-width: 700px;
  }
  .service-editorial .film-description {
    max-width: 540px;
    font-size: 14px;
  }
  .object-annotation {
    position: static;
    align-self: end;
    margin-left: auto;
  }
  .service-shot {
    gap: 50px;
  }
  .narrative-heading {
    font-size: 56px !important;
  }
}
@media (prefers-reduced-motion: reduce) and (max-width: 767px) {
  .service-shot {
    padding: 60px 20px;
  }
  .narrative-heading {
    font-size: 36px !important;
  }
  .object-annotation {
    margin: 35px 0 0;
  }
  .service-editorial .film-description {
    font-size: 12px;
  }
}
</style>
