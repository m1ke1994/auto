<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BurgerMenuButton from './Profile/BurgerMenuButton.vue'
import { MAIN_MENU_ITEMS } from '../data/navigation'
import { getNavigationItems } from '../api/navigation'

const route = useRoute()
const contactsCtaLabel = '\u0421\u0432\u044f\u0437\u0430\u0442\u044c\u0441\u044f \u0441\u043e \u043c\u043d\u043e\u0439'
const menuItems = ref(MAIN_MENU_ITEMS)

const isMenuOpen = ref(false)
const isSticky = ref(false)
const stickySentinel = ref(null)

const isHome = computed(() => route.path === '/')

let observer = null
let useScrollFallback = false

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

const setBodyScrollLock = (locked) => {
  if (typeof document === 'undefined') return
  const overflowValue = locked ? 'hidden' : ''
  document.body.style.overflow = overflowValue
  document.documentElement.style.overflow = overflowValue
}

const handleScroll = () => {
  isSticky.value = window.scrollY > 8
}

const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    closeMenu()
  }
}

const setupStickyObserver = () => {
  if (!('IntersectionObserver' in window) || !stickySentinel.value) {
    useScrollFallback = true
    return
  }

  observer = new IntersectionObserver(
    ([entry]) => {
      isSticky.value = !entry.isIntersecting
    },
    { rootMargin: '-8px 0px 0px 0px', threshold: 0 }
  )
  observer.observe(stickySentinel.value)
}

const loadNavigation = async () => {
  menuItems.value = await getNavigationItems()
}

onMounted(() => {
  loadNavigation()
  setupStickyObserver()
  if (useScrollFallback) {
    window.addEventListener('scroll', handleScroll, { passive: true })
    handleScroll()
  }
  window.addEventListener('keydown', handleKeydown)
})

watch(isMenuOpen, (opened) => {
  setBodyScrollLock(opened)
})

onUnmounted(() => {
  if (useScrollFallback) {
    window.removeEventListener('scroll', handleScroll)
  }
  observer?.disconnect()
  window.removeEventListener('keydown', handleKeydown)
  setBodyScrollLock(false)
})
</script>

<template>
  <div v-if="!isHome" class="app-header">
    <div ref="stickySentinel" class="app-header__sentinel" aria-hidden="true"></div>
    <header class="app-header__bar" :class="{ 'app-header__bar--stuck': isSticky }">
      <div class="app-header__inner">
        <router-link to="/" class="app-header__brand">Новое Конаково</router-link>
        <nav class="app-header__links">
          <template v-for="item in menuItems" :key="item.to || item.href">
            <router-link
              v-if="item.to"
              :to="item.to"
              class="app-header__link"
              active-class="app-header__link--active"
              @click="closeMenu"
            >
              {{ item.label }}
            </router-link>
            <a
              v-else
              :href="item.href"
              class="app-header__link"
              @click="closeMenu"
            >
              {{ item.label }}
            </a>
          </template>
        </nav>

        <div class="app-header__actions">
          <BurgerMenuButton class="app-header__burger" @toggle="toggleMenu" />
        </div>
      </div>
    </header>

    <div class="app-header__spacer" aria-hidden="true"></div>

    <div class="app-header__overlay" :class="{ 'app-header__overlay--show': isMenuOpen }" @click="closeMenu"></div>

    <aside class="app-header__drawer" :class="{ 'app-header__drawer--open': isMenuOpen }">
      <div class="app-header__drawer-head">
        <router-link to="/" class="app-header__drawer-title" @click="closeMenu">Новое Конаково</router-link>
        <button class="app-header__drawer-close" type="button" aria-label="Закрыть меню" @click="closeMenu">×</button>
      </div>
      <template v-for="item in menuItems" :key="item.to || item.href">
        <router-link
          v-if="item.to"
          :to="item.to"
          class="app-header__drawer-link"
          active-class="app-header__drawer-link--active"
          @click="closeMenu"
        >
          {{ item.label }}
        </router-link>
        <a
          v-else
          :href="item.href"
          class="app-header__drawer-link"
          @click="closeMenu"
        >
          {{ item.label }}
        </a>
      </template>
      <router-link class="app-header__drawer-cta btn-primary" to="/contacts" @click="closeMenu">
        {{ contactsCtaLabel }}
      </router-link>
    </aside>
  </div>
</template>

<style scoped>
.app-header {
  position: relative;
  z-index: 80;
}

.app-header__sentinel {
  position: absolute;
  top: 0;
  left: 0;
  width: 1px;
  height: 1px;
}

.app-header__bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 80;
  background: color-mix(in srgb, var(--nav-surface) 65%, transparent);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 22px var(--shadow);
}

.app-header__bar--stuck {
  background: color-mix(in srgb, var(--nav-surface) 80%, transparent);
  box-shadow: 0 16px 30px var(--shadow);
}

.app-header__spacer {
  height: var(--header-h, 72px);
}

.app-header__inner {
  max-width: var(--header-container-max);
  width: 100%;
  margin: 0 auto;
  padding: 12px var(--container-gutter);
  display: flex;
  align-items: center;
  gap: clamp(16px, 1.8vw, 28px);
  box-sizing: border-box;
}

.app-header__brand {
  margin-right: 0;
  color: var(--color-dark-deep);
  font-family: var(--font-brand);
  font-size: clamp(22px, 1.9vw, 30px);
  line-height: 1;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex-shrink: 0;
}

.app-header__links {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1 1 auto;
  flex-wrap: nowrap;
  gap: clamp(12px, 1vw, 24px);
  min-width: 0;
}

.app-header__link {
  font-family: var(--font-menu);
  font-size: var(--font-size-menu);
  font-weight: 500;
  line-height: var(--line-height-tight);
  color: var(--text);
  text-decoration: none;
  position: relative;
  white-space: nowrap;
  padding: 8px 1px;
  transition: color 200ms ease;
}

.app-header__link:hover,
.app-header__link--active {
  color: var(--text-strong);
}

.app-header__link::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -2px;
  height: 2px;
  background: var(--primary);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 220ms ease;
}

.app-header__link:hover::after,
.app-header__link--active::after {
  transform: scaleX(1);
}

.app-header__actions {
  display: none;
  align-items: center;
  gap: 8px;
  margin-left: 0;
  flex-shrink: 0;
}

.app-header__burger {
  display: none;
}

.app-header__overlay {
  position: fixed;
  inset: 0;
  background: rgba(16, 13, 10, 0.45);
  backdrop-filter: blur(2px);
  opacity: 0;
  pointer-events: none;
  transition: opacity 200ms ease;
  z-index: 70;
}

.app-header__overlay--show {
  opacity: 1;
  pointer-events: auto;
}

.app-header__drawer {
  position: fixed;
  top: 0;
  right: 0;
  height: 100dvh;
  width: min(88vw, 360px);
  background: color-mix(in srgb, var(--nav-surface) 88%, transparent);
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(18px);
  transform: translateX(100%);
  transition: transform 250ms ease;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 80;
  box-shadow: 0 24px 50px var(--shadow);
  border-radius: 0;
  overflow-y: auto;
}

.app-header__drawer--open {
  transform: translateX(0);
}

.app-header__drawer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.app-header__drawer-title {
  font-size: clamp(22px, 6vw, 30px);
  color: var(--color-dark-deep);
  font-family: var(--font-brand);
  line-height: 1;
  margin-bottom: 10px;
  letter-spacing: 0.3px;
}

.app-header__drawer-close {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: color-mix(in srgb, var(--card) 76%, transparent);
  color: var(--text);
  font-size: 20px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.app-header__drawer-link {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: none;
  color: var(--text);
  font-family: var(--font-menu);
  font-size: var(--font-size-small);
  font-weight: 500;
  line-height: 1.3;
  position: relative;
  transition: color 200ms ease, background 200ms ease, transform 200ms ease;
}

.app-header__drawer-link:hover,
.app-header__drawer-link--active {
  color: var(--text-strong);
}

.app-header__drawer-link:active {
  transform: scale(0.99);
}

.app-header__drawer-cta {
  margin-top: auto;
  width: 100%;
}

@media (max-width: 1200px) {
  .app-header__brand {
    display: none;
  }

  .app-header__links {
    display: none;
  }

  .app-header__bar {
    background: transparent;
    border-bottom: none;
    box-shadow: none;
    backdrop-filter: none;
  }

  .app-header__bar--stuck {
    background: transparent;
    box-shadow: none;
  }

  .app-header__inner {
    padding: 12px var(--container-gutter-mobile);
  }

  .app-header__actions {
    display: inline-flex;
    margin-left: auto;
  }

  .app-header__brand {
    font-size: clamp(20px, 6.4vw, 28px);
    margin-right: 10px;
  }

  .app-header__burger {
    display: inline-flex;
  }

  .app-header__spacer {
    height: 68px;
  }
}

@media (max-width: 414px) {
  .app-header__inner {
    padding: 10px var(--container-gutter-mobile);
  }

  .app-header__brand {
    font-size: clamp(19px, 7vw, 25px);
  }

  .app-header__drawer {
    width: min(92vw, 340px);
  }
}
</style>
