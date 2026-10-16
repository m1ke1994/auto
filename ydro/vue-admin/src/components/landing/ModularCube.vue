<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
const props = defineProps({
  active: { type: Number, default: -1 },
  assemble: Boolean,
  cinematic: Boolean,
  portrait: Boolean,
  take: { type: Number, default: 0 },
  progress: { type: Number, default: 0 },
  services: { type: Array, default: () => [] },
})
const host = ref(null)
const ready = ref(false)
const anchors = ref([])
let scene,
  observer,
  disposed = false
onMounted(() => {
  observer = new IntersectionObserver(
    async ([entry]) => {
      if (!entry.isIntersecting || scene || disposed) return
      observer.disconnect()
      try {
        const { createCube } = await import('./cubeScene.js')
        if (disposed) return
        scene = createCube(
          host.value,
          () => {
            ready.value = false
          },
          props.services.length ? (points) => { anchors.value = points } : null,
        )
        scene.setPortrait(props.portrait)
        scene.setTake(props.take)
        scene.setCinematic(props.cinematic)
        scene.setProgress(props.progress)
        scene.setActive(props.active)
        scene.setAssemble(props.assemble)
        ready.value = true
      } catch {
        /* Static sculpture remains available without WebGL or a downloaded chunk. */
      }
    },
    { rootMargin: '120px' },
  )
  observer.observe(host.value)
})
watch(
  () => props.active,
  (value) => scene?.setActive(value),
)
watch(
  () => props.assemble,
  (value) => scene?.setAssemble(value),
)
watch(
  () => props.progress,
  (value) => scene?.setProgress(value),
)
watch(
  () => props.cinematic,
  (value) => scene?.setCinematic(value),
)
watch(
  () => props.portrait,
  (value) => scene?.setPortrait(value),
)
watch(
  () => props.take,
  (value) => scene?.setTake(value),
)
onBeforeUnmount(() => {
  disposed = true
  observer?.disconnect()
  scene?.dispose()
})
</script>
<template>
  <div ref="host" class="cube-host" :class="{ cinematic }">
    <div class="cube-static" aria-hidden="true" :class="{ concealed: ready }">
      <div class="static-object">
        <span v-for="n in 9" :key="n" :class="{ blue: n === 5 }"></span>
      </div>
    </div>
    <div
      v-if="cinematic && ready && progress > 0.36"
      class="service-labels"
      :style="{ opacity: Math.min(1, (progress - 0.36) / 0.14) }"
    >
      <span
        v-for="(service, index) in services"
        :key="service.title"
        class="service-label"
        :class="{ selected: active === index }"
        :style="{
          left: (anchors[index]?.x ?? 50) + '%',
          top: (anchors[index]?.y ?? 50) + '%',
        }"
        ><i>0{{ index + 1 }}</i
        >{{ service.title }}</span
      >
    </div>
  </div>
</template>
<style scoped>
.cube-host {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 220px;
  contain: layout paint;
}
.service-labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.service-label {
  position: absolute;
  transform: translate(-50%, 32px);
  display: flex;
  align-items: center;
  gap: 9px;
  white-space: nowrap;
  padding: 8px 12px;
  border: 1px solid #ffffff1c;
  border-radius: 5px;
  background: #101724e8;
  color: #a6b4cc;
  font-size: 11px;
  letter-spacing: 0.2px;
  transition:
    color 0.3s,
    border-color 0.3s;
}
.service-label i {
  font-style: normal;
  color: #5f80b5;
  font-size: 9px;
}
.service-label.selected {
  color: #e6efff;
  border-color: #6899f1;
  background: #172a4de8;
}
.service-label.selected i {
  color: #8db4ff;
}
.cube-host :deep(canvas) {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.cube-static {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  transition: opacity 0.3s;
}
.cube-static.concealed {
  opacity: 0;
}
.static-object {
  width: 53%;
  aspect-ratio: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  transform: perspective(650px) rotateX(22deg) rotateY(-30deg) rotateZ(9deg);
  filter: drop-shadow(25px 38px 22px #0008);
}
.static-object span {
  border-radius: 9%;
  background: linear-gradient(135deg, #a6afbd, #394451 48%, #171e29);
  border: 1px solid #abb9cd66;
  box-shadow: 8px 6px 0 #1a222d;
}
.static-object .blue {
  background: linear-gradient(135deg, #a7c7ff, #3979ff 50%, #1748ba);
  box-shadow: 8px 6px 0 #12326b;
}
@media (max-width: 767px) {
  .service-label {
    font-size: 10px;
    padding: 6px 9px;
    transform: translate(-50%, 27px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .cube-static {
    transition: none;
  }
}
</style>
