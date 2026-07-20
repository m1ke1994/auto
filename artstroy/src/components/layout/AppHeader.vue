<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isMenuOpen = ref(false)
const activeSection = ref('about')

const navItems = [
  { id: 'about', label: 'О компании', target: 'about' },
  { id: 'projects', label: 'Наши проекты', target: 'projects' },
  { id: 'reviews', label: 'Отзывы', target: 'reviews' },
  { id: 'contacts', label: 'Контакты', target: 'contacts' },
]

const closeMenu = () => {
  isMenuOpen.value = false
}

const scrollToSection = (target, behavior = 'smooth') => {
  const section = document.getElementById(target)
  if (!section) return

  section.scrollIntoView({
    behavior,
    block: 'start',
  })
}

const navigateToSection = async (target) => {
  closeMenu()
  activeSection.value = target

  if (route.path !== '/') {
    await router.push({ path: '/', hash: `#${target}` })
    return
  }

  scrollToSection(target)
}

const syncFromHash = async () => {
  if (route.path !== '/' || !route.hash) return

  const target = route.hash.replace('#', '')
  await nextTick()
  window.setTimeout(() => scrollToSection(target), 80)
}

const updateActiveSection = () => {
  if (route.path !== '/') return

  const ids = ['about', 'projects', 'reviews', 'contacts']
  const markerY = window.scrollY + 140
  let current = 'about'

  for (const id of ids) {
    const section = document.getElementById(id)
    if (section && markerY >= section.offsetTop) {
      current = id
    }
  }

  activeSection.value = current
}

watch(
  () => route.fullPath,
  async () => {
    await syncFromHash()
    updateActiveSection()
    closeMenu()
  },
)

watch(isMenuOpen, (opened) => {
  document.body.style.overflow = opened ? 'hidden' : ''
})

onMounted(async () => {
  await syncFromHash()
  updateActiveSection()
  window.addEventListener('scroll', updateActiveSection, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateActiveSection)
  document.body.style.overflow = ''
})
</script>

<template>
  <header class="header-shell fixed inset-x-0 top-0 z-[90] px-3 pt-3 sm:px-5 sm:pt-4 lg:px-8 lg:pt-4">
    <div
      class="mx-auto flex  w-full max-w-[1440px] items-center justify-between rounded-[1.1rem] border border-white/65 bg-[#f8fafc]/62 px-2 shadow-[0_12px_28px_rgba(15,23,42,0.09)] backdrop-blur-[14px] sm:h-[5.5rem] sm:px-4 lg:h-[7rem] lg:px-4"
    >
      <RouterLink
        to="/"
        class="flex h-[4.375rem] w-[4.375rem] shrink-0 items-center justify-center rounded-full border border-[#5b6169]/25 bg-white/75 p-[0.1875rem] shadow-[0_6px_16px_rgba(15,23,42,0.08)] transition duration-200 hover:bg-white lg:h-[4.25rem] lg:w-[4.25rem]"
      >
        <img
          src="/logo/logo.png"
          alt="Логотип компании"
          class="h-full w-full rounded-full object-cover"
        />
      </RouterLink>

      <nav class="hidden items-center gap-1 lg:flex">
        <button
          v-for="item in navItems"
          :key="item.id"
          type="button"
          class="rounded-full px-4 py-2 text-[1rem] font-medium transition duration-200 xl:text-[1.0625rem]"
          :class="activeSection === item.id
            ? 'bg-white/84 text-[#111827] shadow-[0_7px_18px_rgba(15,23,42,0.1)]'
            : 'text-[#4b5563] hover:bg-white/72 hover:text-[#111827]'"
          @click="navigateToSection(item.target)"
        >
          {{ item.label }}
        </button>
      </nav>

      <button
        type="button"
        class="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[#5b6169]/25 bg-white/70 text-[#111827] transition duration-200 hover:bg-white lg:hidden"
        aria-label="Открыть меню"
        @click="isMenuOpen = true"
      >
        <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>
    </div>

    <Transition name="mobile-nav">
      <div
        v-if="isMenuOpen"
        class="fixed inset-0 z-[100] bg-[#f3f5f8]/55 backdrop-blur-[4px] lg:hidden"
        @click.self="closeMenu"
      >
        <div
          class="mx-auto mt-20 w-[min(92%,28rem)] rounded-[1.25rem] border border-white/72 bg-[#f9fbfe]/76 p-5 shadow-[0_20px_50px_rgba(15,23,42,0.14)] backdrop-blur-[16px] sm:mt-24 sm:p-6"
        >
          <div class="mb-4 flex items-center justify-between">
            <p class="text-[0.875rem] font-semibold uppercase tracking-[0.14em] text-[#6b7280]">
              Навигация
            </p>

            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#5b6169]/25 bg-white/72 text-[#111827] transition hover:bg-white"
              aria-label="Закрыть меню"
              @click="closeMenu"
            >
              <svg viewBox="0 0 24 24" class="h-4.5 w-4.5" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M18 6 6 18" />
              </svg>
            </button>
          </div>

          <nav class="flex flex-col gap-2">
            <button
              v-for="item in navItems"
              :key="`mobile-${item.id}`"
              type="button"
              class="w-full rounded-[0.95rem] border px-4 py-3 text-left text-[1.06rem] font-medium transition duration-200"
              :class="activeSection === item.id
                ? 'border-[#4b5563]/32 bg-white text-[#111827] shadow-[0_8px_18px_rgba(15,23,42,0.08)]'
                : 'border-[#5b6169]/18 bg-white/70 text-[#4b5563] hover:border-[#5b6169]/30 hover:text-[#111827]'"
              @click="navigateToSection(item.target)"
            >
              {{ item.label }}
            </button>
          </nav>
        </div>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.header-shell {
  font-family: "Manrope", "Segoe UI", sans-serif;
}

.mobile-nav-enter-active,
.mobile-nav-leave-active {
  transition: opacity 0.28s ease;
}

.mobile-nav-enter-from,
.mobile-nav-leave-to {
  opacity: 0;
}
</style>
