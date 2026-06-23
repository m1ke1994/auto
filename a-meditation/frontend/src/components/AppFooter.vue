<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

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
  site: {
    type: Object,
    default: null,
  },
})

const fallbackNavLinks = [
  { label: 'Простыми словами', target: 'simple-words' },
  { label: 'Проводник Лилы', target: 'guide' },
  { label: 'Отзывы', target: 'reviews' },
  { label: 'Стоимость', target: 'pricing' },
]

const fallbackContactLinks = [
  { label: 'Записаться на игру', target: 'contacts' },
  { label: 'Telegram', href: '#' },
  { label: 'WhatsApp', href: '#' },
]

const footerContent = computed(() => props.section?.content || {})
const navLinks = computed(() => {
  const links = footerContent.value.navigation_links
  if (!Array.isArray(links) || links.length === 0) return fallbackNavLinks
  return links
    .filter((link) => link?.label && link?.href)
    .map((link) => ({
      label: link.label,
      target: String(link.href).replace(/^#/, ''),
    }))
})
const footerText = computed(
  () => footerContent.value.text || 'Игра Лила в Москве — путь к ясности через честный диалог с собой.',
)
const copyrightText = computed(() => footerContent.value.copyright || '© 2026 Все права защищены.')
const navigationTitle = computed(() => footerContent.value.navigation_title || 'Навигация')
const contactsTitle = computed(() => footerContent.value.contacts_title || 'Контакты')
const contactLinks = computed(() => {
  const links = footerContent.value.links
  if (!Array.isArray(links) || links.length === 0) {
    return fallbackContactLinks
  }
  return links.map((link) => ({
    label: link.label || 'Ссылка',
    target: String(link.href || '').startsWith('#') ? String(link.href).slice(1) : '',
    href: String(link.href || '').startsWith('#') ? '' : link.href || '',
    targetMode: link.target || '_self',
  }))
})
const footerBrand = computed(() => (footerContent.value.brand || props.site?.name || 'ЛИЛА МОСКВА').toUpperCase())

const modelUrl = '/models/dice.glb'

let THREE
let GLTFLoader
let scene
let camera
let renderer
let diceModel
let resizeObserver
let animationFrameId = 0
let diceMediaQuery
let diceObserver

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

function scrollToSection(target) {
  const section = document.getElementById(target)

  if (section) {
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleContactClick(item) {
  if (item.target) {
    scrollToSection(item.target)
    return
  }
  if (item.href) {
    const mode = item.targetMode === '_blank' ? '_blank' : '_self'
    window.open(item.href, mode, mode === '_blank' ? 'noopener,noreferrer' : undefined)
  }
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

const resizeRenderer = () => {
  if (!renderer || !camera || !diceContainer.value) return

  const width = Math.max(diceContainer.value.clientWidth, 1)
  const height = Math.max(diceContainer.value.clientHeight, 1)

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
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

  if (diceModel) {
    const time = performance.now() * 0.001

    diceModel.rotation.x = 0.35 + Math.sin(time * 0.7) * 0.08
    diceModel.rotation.y += 0.012
    diceModel.rotation.z = 0.08
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

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100)
  camera.position.set(0, 0, 4.9)

  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.setClearColor(0x000000, 0)
  renderer.domElement.className = 'block h-full w-full'
  renderer.domElement.setAttribute('aria-hidden', 'true')
  diceContainer.value.appendChild(renderer.domElement)

  const ambientLight = new THREE.AmbientLight(0xffffff, 1.9)
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.3)
  const rimLight = new THREE.DirectionalLight(0xffffff, 1.2)

  keyLight.position.set(2.2, 3, 4)
  rimLight.position.set(-2.8, 1.2, 2.4)
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

  animate()
}

const cleanupThree = () => {
  window.removeEventListener('resize', resizeRenderer)

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

const observeDiceContainer = () => {
  if (!diceContainer.value || !canRenderDiceModel.value || renderer) return

  if (!('IntersectionObserver' in window)) {
    initThree()
    return
  }

  diceObserver?.disconnect()
  diceObserver = new IntersectionObserver(
    ([entry]) => {
      if (!entry.isIntersecting) return

      diceObserver?.disconnect()
      diceObserver = null
      initThree()
    },
    {
      rootMargin: '420px 0px',
      threshold: 0.01,
    },
  )

  diceObserver.observe(diceContainer.value)
}

const updateDiceRenderMode = () => {
  canRenderDiceModel.value = Boolean(diceMediaQuery?.matches)

  if (canRenderDiceModel.value) {
    observeDiceContainer()
  } else {
    diceObserver?.disconnect()
    diceObserver = null
    cleanupThree()
  }
}

onMounted(() => {
  diceMediaQuery = window.matchMedia('(min-width: 1024px) and (pointer: fine)')
  addMediaQueryListener(diceMediaQuery, updateDiceRenderMode)
  updateDiceRenderMode()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeRenderer)
  removeMediaQueryListener(diceMediaQuery, updateDiceRenderMode)

  diceObserver?.disconnect()
  cleanupThree()
})
</script>

<template>
  <footer class="relative overflow-hidden border-t border-white/10 bg-[#24231F] text-white">
        
    <div class="relative mx-auto max-w-[1280px] px-6 py-10 md:px-8 md:py-12">
    <div class="grid gap-10 md:grid-cols-3 md:items-start md:justify-items-center">
        <!-- Logo -->
 <div class="space-y-5 md:justify-self-start">
          <RouterLink
            to="/"
            class="inline-flex items-center gap-2 text-sm font-semibold uppercase leading-none tracking-[0.22em] text-white"
            :aria-label="footerBrand"
          >
            <span>{{ footerBrand.split(' ')[0] || 'ЛИЛА' }}</span>

            <span
              ref="diceContainer"
              class="relative -my-4 flex h-14 w-14 shrink-0 items-center justify-center overflow-visible md:h-16 md:w-16"
              role="img"
              aria-label="3D кубик"
            >
              <img
                v-if="!canRenderDiceModel"
                src="/dice.png"
                alt=""
                class="h-9 w-9 object-contain opacity-95 md:h-10 md:w-10"
                loading="lazy"
                decoding="async"
                aria-hidden="true"
              >
            </span>

            <span>{{ footerBrand.split(' ').slice(1).join(' ') || 'МОСКВА' }}</span>
          </RouterLink>

          <p class="text-sm leading-6 text-white/70">
            {{ copyrightText }}
          </p>
        </div>

        <!-- Navigation -->
        <div class="md:justify-self-center">
          <h2 class="mb-4 text-xs font-semibold uppercase tracking-[0.22em] text-white/70">
            {{ navigationTitle }}
          </h2>

          <nav class="flex flex-col gap-2.5 text-sm text-white/70">
            <button
              v-for="item in navLinks"
              :key="item.target"
              type="button"
              class="w-fit text-left transition hover:translate-x-0.5 hover:text-[#8B7449]"
              @click="scrollToSection(item.target)"
            >
              {{ item.label }}
            </button>
          </nav>
        </div>

        <!-- Contacts -->
       <div class="md:justify-self-end">
          <h2 class="mb-4 text-xs font-semibold uppercase tracking-[0.22em] text-white/70">
            {{ contactsTitle }}
          </h2>

          <nav class="flex flex-col gap-2.5 text-sm text-white/70">
            <button
              v-for="item in contactLinks"
              :key="item.label"
              type="button"
              class="w-fit text-left transition hover:translate-x-0.5 hover:text-[#8B7449]"
              @click="handleContactClick(item)"
            >
              {{ item.label }}
            </button>
          </nav>
        </div>
      </div>

      <div class="mt-9 border-t border-white pt-5 text-sm leading-6 text-white/75">
        {{ footerText }}
      </div>
    </div>
  </footer>
</template>
