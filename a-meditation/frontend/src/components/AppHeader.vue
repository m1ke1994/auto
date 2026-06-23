<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const isOpen = ref(false)
const hasScrolled = ref(false)
const diceContainer = ref(null)
const canRenderDiceModel = ref(
  typeof window !== 'undefined' &&
    window.matchMedia('(min-width: 1024px) and (pointer: fine)').matches,
)

const props = defineProps({
  section: {
    type: Object,
    default: null,
  },
})

const fallbackLeftMenuItems = [
  { label: ' ПРО ЛИЛУ', targetId: 'simple-words' },
  { label: 'ПРОВОДНИК ЛИЛЫ', targetId: 'guide' },
  { label: 'ОТЗЫВЫ', targetId: 'reviews' },
]
const fallbackRightMenuItems = [
  { label: 'МЕДИТАЦИИ', targetId: 'meditations' },
  { label: 'СТОИМОСТЬ', targetId: 'pricing' },
  { label: 'КОНТАКТЫ', targetId: 'contacts' },
]
const sectionContent = computed(() => props.section?.content || {})

function normalizeLinks(links, fallback) {
  if (!Array.isArray(links) || links.length === 0) return fallback
  return links
    .filter((item) => item?.label && item?.href)
    .map((item) => ({
      label: item.label,
      targetId: String(item.href).replace(/^#/, ''),
    }))
}

const leftMenuItems = computed(() => normalizeLinks(sectionContent.value.left_links, fallbackLeftMenuItems))
const rightMenuItems = computed(() => normalizeLinks(sectionContent.value.right_links, fallbackRightMenuItems))
const mobileMenuItems = computed(() => [...leftMenuItems.value, ...rightMenuItems.value])
const brandLeft = computed(() => sectionContent.value.brand_left || 'ЛИЛА')
const brandRight = computed(() => sectionContent.value.brand_right || 'МОСКВА')

const modelUrl = '/models/dice.glb'

let THREE
let GLTFLoader
let scene
let camera
let renderer
let diceModel
let resizeObserver
let animationFrameId = 0
let isMobileDevice = false
let pointerX = 0
let pointerY = 0
let diceMediaQuery

const addMediaQueryListener = (query, listener) => {
  if (!query) return
  if (typeof query.addEventListener === 'function') {
    query.addEventListener('change', listener)
  } else {
    query.addListener(listener)
  }
}

const removeMediaQueryListener = (query, listener) => {
  if (!query) return
  if (typeof query.removeEventListener === 'function') {
    query.removeEventListener('change', listener)
  } else {
    query.removeListener(listener)
  }
}

const loadThreeRuntime = async () => {
  if (THREE && GLTFLoader) return

  const [threeModule, gltfLoaderModule] = await Promise.all([
    import('three'),
    import('three/examples/jsm/loaders/GLTFLoader.js'),
  ])

  THREE = threeModule
  GLTFLoader = gltfLoaderModule.GLTFLoader
}

const toggleMenu = () => {
  isOpen.value = !isOpen.value
}

const closeMenu = () => {
  isOpen.value = false
}

const scrollToSection = (item) => {
  if (!item.targetId) {
    closeMenu()
    return
  }

  document.getElementById(item.targetId)?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
  closeMenu()
}

const handleScroll = () => {
  hasScrolled.value = window.scrollY > 8
}

const handlePointerMove = (event) => {
  if (isMobileDevice) return

  pointerX = (event.clientX / window.innerWidth - 0.5) * 2
  pointerY = (event.clientY / window.innerHeight - 0.5) * 2
}

const resizeRenderer = () => {
  if (!renderer || !camera || !diceContainer.value) return

  const { clientWidth, clientHeight } = diceContainer.value
  const width = Math.max(clientWidth, 1)
  const height = Math.max(clientHeight, 1)

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(width, height, false)

  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

const centerAndScaleModel = (model) => {
  const box = new THREE.Box3().setFromObject(model)
  const size = box.getSize(new THREE.Vector3())
  const center = box.getCenter(new THREE.Vector3())
  const maxAxis = Math.max(size.x, size.y, size.z) || 1

  model.position.sub(center)
  model.position.y += 0.7
  model.scale.setScalar(2 / maxAxis)
}

const disposeModel = (object) => {
  object.traverse((child) => {
    if (child.geometry) {
      child.geometry.dispose()
    }

    if (child.material) {
      const materials = Array.isArray(child.material) ? child.material : [child.material]

      materials.forEach((material) => {
        Object.values(material).forEach((value) => {
          if (value && typeof value.dispose === 'function') {
            value.dispose()
          }
        })
        material.dispose()
      })
    }
  })
}

const animate = () => {
  if (!renderer || !scene || !camera) return

  const time = performance.now() * 0.001

  if (diceModel) {
    const targetX = isMobileDevice ? 0.35 + Math.sin(time * 0.9) * 0.12 : 0.35 - pointerY * 0.62
    const targetY = isMobileDevice ? time * 0.75 : 0.55 + pointerX * 1.15
    const targetZ = isMobileDevice ? 0.08 : 0.08 + pointerX * 0.2 - pointerY * 0.12

    diceModel.rotation.x += (targetX - diceModel.rotation.x) * 0.09
    diceModel.rotation.y += (targetY - diceModel.rotation.y) * 0.09
    diceModel.rotation.z += (targetZ - diceModel.rotation.z) * 0.09
  }

  renderer.render(scene, camera)
  animationFrameId = window.requestAnimationFrame(animate)
}

const initThree = async () => {
  if (!diceContainer.value || !canRenderDiceModel.value || renderer) return

  try {
    await loadThreeRuntime()
  } catch (error) {
    console.warn('Не удалось загрузить Three.js для 3D-кубика', error)
    canRenderDiceModel.value = false
    return
  }

  if (!diceContainer.value || !canRenderDiceModel.value || renderer) return

  isMobileDevice = window.matchMedia('(pointer: coarse)').matches

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100)
  camera.position.set(0, 0, 5)

  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.setClearColor(0x000000, 0)
  renderer.domElement.className = 'block h-full w-full'
  renderer.domElement.setAttribute('aria-hidden', 'true')
  diceContainer.value.appendChild(renderer.domElement)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.8)
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.4)
  const rimLight = new THREE.DirectionalLight(0xbfd7ff, 1.5)

  keyLight.position.set(2.4, 3, 4)
  rimLight.position.set(-3, 1.5, 2)
  scene.add(ambientLight, keyLight, rimLight)

  const loader = new GLTFLoader()
  loader.load(
    modelUrl,
    (gltf) => {
      diceModel = gltf.scene
      centerAndScaleModel(diceModel)
      diceModel.rotation.set(0.35, 0.55, 0.08)
      scene.add(diceModel)
    },
    undefined,
    (error) => {
      console.warn(`Не удалось загрузить 3D-модель кубика: ${modelUrl}`, error)
    },
  )

  resizeRenderer()
  resizeObserver = new ResizeObserver(resizeRenderer)
  resizeObserver.observe(diceContainer.value)
  window.addEventListener('resize', resizeRenderer)
  window.addEventListener('pointermove', handlePointerMove, { passive: true })

  animate()
}

const cleanupThree = () => {
  window.removeEventListener('resize', resizeRenderer)
  window.removeEventListener('pointermove', handlePointerMove)

  if (animationFrameId) {
    window.cancelAnimationFrame(animationFrameId)
    animationFrameId = 0
  }

  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }

  if (diceModel && scene) {
    disposeModel(diceModel)
    scene.remove(diceModel)
    diceModel = null
  }

  if (renderer) {
    renderer.dispose()
    renderer.forceContextLoss()

    if (renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }

  renderer = null
  camera = null
  scene = null
}

const updateDiceRenderMode = () => {
  canRenderDiceModel.value = Boolean(diceMediaQuery?.matches)

  if (canRenderDiceModel.value) {
    initThree()
  } else {
    cleanupThree()
  }
}

onMounted(() => {
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive: true })
  diceMediaQuery = window.matchMedia('(min-width: 1024px) and (pointer: fine)')
  addMediaQueryListener(diceMediaQuery, updateDiceRenderMode)
  updateDiceRenderMode()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', resizeRenderer)
  window.removeEventListener('pointermove', handlePointerMove)
  removeMediaQueryListener(diceMediaQuery, updateDiceRenderMode)

  cleanupThree()
})
</script>

<template>
  <header
    class="fixed left-0 top-0 z-50 w-full border-b border-white/10 text-white transition duration-300"
    :class="hasScrolled ? 'bg-zinc-950/[0.78] shadow-2xl shadow-black/25 backdrop-blur-2xl' : 'bg-zinc-900/[0.58] shadow-lg shadow-black/10 backdrop-blur-xl'"
  >
    <div class="mx-auto grid h-16 max-w-[1280px] grid-cols-[1fr_auto_1fr] items-center px-6 md:h-[72px] md:px-8">
      <nav class="hidden items-center justify-start gap-5 text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-200 md:flex lg:gap-6 xl:gap-7">
        <a
          v-for="item in leftMenuItems"
          :key="item.label"
          href="#"
          class="transition hover:text-white hover:drop-shadow-[0_0_10px_rgba(255,255,255,0.22)]"
          @click.prevent="scrollToSection(item)"
        >
          {{ item.label }}
        </a>
      </nav>

      <a
        href="#top"
        class="flex items-center justify-center gap-2.5 justify-self-center whitespace-nowrap text-[13px] font-semibold uppercase leading-none tracking-[0.22em] text-white sm:text-sm md:text-base"
        aria-label="Лила Москва"
        @click="closeMenu"
      >
        <span>{{ brandLeft }}</span>
        <span
          ref="diceContainer"
          class="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-visible md:h-16 md:w-16"
          role="img"
          aria-label="3D кубик"
        >
          <img
            v-if="!canRenderDiceModel"
            src="/dice.png"
            alt=""
            class="h-9 w-9 object-contain opacity-95 md:h-10 md:w-10"
            loading="eager"
            decoding="async"
            aria-hidden="true"
          >
        </span>
        <span>{{ brandRight }}</span>
      </a>

      <nav class="hidden items-center justify-end gap-5 text-[11px] font-medium uppercase tracking-[0.18em] text-zinc-200 md:flex lg:gap-6 xl:gap-7">
        <a
          v-for="item in rightMenuItems"
          :key="item.label"
          href="#"
          class="transition hover:text-white hover:drop-shadow-[0_0_10px_rgba(255,255,255,0.22)]"
          @click.prevent="scrollToSection(item)"
        >
          {{ item.label }}
        </a>
      </nav>

      <button
        type="button"
        class="col-start-3 inline-flex h-10 w-10 items-center justify-center justify-self-end rounded-full border border-white/20 bg-white/10 text-white shadow-lg shadow-black/10 backdrop-blur transition hover:border-white/35 hover:bg-white/15 md:hidden"
        :aria-expanded="isOpen"
        aria-controls="mobile-menu"
        aria-label="Открыть меню"
        @click="toggleMenu"
      >
        <span class="relative block h-4 w-5">
          <span
            class="absolute left-0 top-0 h-0.5 w-5 bg-current transition duration-300"
            :class="isOpen ? 'translate-y-[7px] rotate-45' : ''"
          />
          <span
            class="absolute left-0 top-[7px] h-0.5 w-5 bg-current transition duration-300"
            :class="isOpen ? 'opacity-0' : 'opacity-100'"
          />
          <span
            class="absolute bottom-0 left-0 h-0.5 w-5 bg-current transition duration-300"
            :class="isOpen ? '-translate-y-[7px] -rotate-45' : ''"
          />
        </span>
      </button>
    </div>

    <Transition
      enter-active-class="transition duration-[250ms] ease-out"
      enter-from-class="opacity-0 -translate-y-4 scale-[0.98]"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 -translate-y-4 scale-[0.98]"
    >
      <nav
        v-if="isOpen"
        id="mobile-menu"
        class="mx-4 mb-4 flex flex-col gap-1 rounded-3xl border border-white/10 bg-zinc-950/[0.88] px-5 py-5 text-center text-sm font-medium uppercase tracking-[0.2em] text-white shadow-2xl shadow-black/35 backdrop-blur-2xl md:hidden"
      >
        <a
          v-for="item in mobileMenuItems"
          :key="item.label"
          href="#"
          class="rounded-2xl px-4 py-3 text-zinc-200 transition hover:bg-white/10 hover:text-white"
          @click.prevent="scrollToSection(item)"
        >
          {{ item.label }}
        </a>
      </nav>
    </Transition>
  </header>
</template>
