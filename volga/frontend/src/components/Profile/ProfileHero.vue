<template>
    <div class="hero">
        <div class="hero-nav__overlay" :class="{ 'hero-nav__overlay--show': isMenuOpen }" @click="closeMenu"></div>
        <aside class="hero-nav__drawer" :class="{ 'hero-nav__drawer--open': isMenuOpen }">
            <div class="hero-nav__drawer-head">
                <router-link to="/" class="hero-nav__drawer-title" @click="closeMenu">Новое Конаково</router-link>
                <button class="hero-nav__drawer-close" type="button" aria-label="Закрыть меню" @click="closeMenu">×</button>
            </div>
            <template v-for="item in menuItems" :key="item.to || item.href">
                <router-link
                    v-if="item.to"
                    :to="item.to"
                    class="hero-nav__drawer-link"
                    active-class="hero-nav__drawer-link--active"
                    @click="closeMenu"
                >
                    {{ item.label }}
                </router-link>
                <a
                    v-else
                    :href="item.href"
                    class="hero-nav__drawer-link"
                    @click="closeMenu"
                >
                    {{ item.label }}
                </a>
            </template>
            <router-link class="hero-nav__drawer-cta btn-primary" to="/contacts" @click="closeMenu">
                Связаться со мной
            </router-link>
        </aside>

        <div class="hero__top" :style="heroTopStyle">
            <div ref="stickySentinel" class="hero__sentinel" aria-hidden="true"></div>
            <header class="hero-nav" :class="{ 'hero-nav--stuck': isSticky }">
                <div class="hero-nav__inner">
                    <router-link to="/" class="hero-nav__brand">Новое Конаково</router-link>

                    <nav class="hero-nav__links">
                        <template v-for="item in menuItems" :key="item.to || item.href">
                            <router-link
                                v-if="item.to && !item.mobileOnly"
                                :to="item.to"
                                class="hero-nav__link"
                                active-class="hero-nav__link--active"
                            >
                                {{ item.label }}
                            </router-link>
                            <a
                                v-else-if="!item.mobileOnly"
                                :href="item.href"
                                class="hero-nav__link"
                            >
                                {{ item.label }}
                            </a>
                        </template>
                    </nav>

                    <div class="hero-nav__actions">
                        <BurgerMenuButton class="hero-nav__burger" @toggle="toggleMenu" />
                    </div>
                </div>
            </header>
            <div class="hero__project-title">Новое Конаково</div>
        </div>

        <div class="hero__bottom">
            <div class="avatar" v-reveal>
                <img
                    v-if="heroAvatarSrc"
                    :src="heroAvatarSrc"
                    alt="Фото"
                    loading="lazy"
                    decoding="async"
                    width="190"
                    height="190"
                    class="img-lazy"
                    @load="markImageLoaded"
                >
                <div v-else class="avatar__placeholder">Фото</div>
            </div>
            <div class="info" v-reveal.delay="120">
                <div class="info__name">{{ displayTitle }}</div>
                <div class="info__row">
                    <div v-if="loadingHero" class="info__status">Загрузка Hero...</div>
                    <div v-else-if="heroError" class="info__status">Hero временно недоступен. Показаны запасные данные.</div>
                    <RichText :content="displayDescription" class="info__about" />
                    <router-link class="info__btn btn-primary" to="/contacts">Связаться со мной</router-link>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import BurgerMenuButton from './BurgerMenuButton.vue'
import { useHero } from '../../composables/useHero'
import RichText from '../ui/RichText.vue';

defineProps({
    menuItems: { type: Array, required: true },
})

const isMenuOpen = ref(false)
const isSticky = ref(false)
const stickySentinel = ref(null)
const { hero, loadingHero, heroError, loadHero } = useHero()

let observer = null
let preloadLink = null
let useScrollFallback = false
const fallbackTitle = 'Гость Конаково'
const fallbackDescription = 'Делюсь событиями, тишиной и тёплыми практиками в Конаково.'

const heroBackgroundImage = computed(() => hero.value?.background_image || '')
const heroAvatarSrc = computed(() => hero.value?.avatar || '')
const displayTitle = computed(() => hero.value?.title || fallbackTitle)
const displayDescription = computed(() => hero.value?.description || fallbackDescription)
const heroTopStyle = computed(() => ({
    backgroundImage: heroBackgroundImage.value
        ? `url(${heroBackgroundImage.value})`
        : 'none',
}))

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

const handleKeydown = (event) => {
    if (event.key === 'Escape') {
        closeMenu()
    }
}

const handleScroll = () => {
    isSticky.value = window.scrollY > 8
}

const markImageLoaded = (event) => {
    event.target.classList.add('is-loaded')
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

const setupHeroPreload = () => {
    if (typeof document === 'undefined' || !heroBackgroundImage.value) return
    preloadLink = document.createElement('link')
    preloadLink.rel = 'preload'
    preloadLink.as = 'image'
    preloadLink.href = heroBackgroundImage.value
    document.head.appendChild(preloadLink)
}

onMounted(async () => {
    await loadHero()
    setupHeroPreload()
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

watch(heroBackgroundImage, () => {
    preloadLink?.remove()
    setupHeroPreload()
})

onUnmounted(() => {
    observer?.disconnect()
    if (useScrollFallback) {
        window.removeEventListener('scroll', handleScroll)
    }
    window.removeEventListener('keydown', handleKeydown)
    preloadLink?.remove()
    setBodyScrollLock(false)
})
</script>

<style scoped>
.hero {
    position: relative;
}

.hero__sentinel {
    position: absolute;
    top: 0;
    left: 0;
    width: 1px;
    height: 1px;
}

.hero-nav {
    position: sticky;
    top: 16px;
    z-index: 60;
    width: min(var(--header-container-max), calc(100% - 32px));
    margin: 16px auto 0;
    border-radius: 12px;
    background: color-mix(in srgb, var(--nav-surface) 60%, transparent);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(18px);
    box-shadow: 0 12px 26px var(--shadow);
    transition: box-shadow 200ms ease, background 200ms ease, transform 200ms ease;
}

.hero-nav--stuck {
    background: color-mix(in srgb, var(--nav-surface) 75%, transparent);
    box-shadow: 0 18px 36px var(--shadow);
}

.hero-nav__inner {
    padding: 10px var(--container-gutter);
    display: flex;
    align-items: center;
    gap: clamp(16px, 1.8vw, 28px);
    box-sizing: border-box;
}

.hero-nav__brand {
    margin-right: 0;
    color: var(--color-dark-deep);
    font-family: var(--font-brand);
    font-size: clamp(22px, 1.9vw, 30px);
    line-height: 1;
    letter-spacing: 0.4px;
    text-shadow: none;
    white-space: nowrap;
    flex-shrink: 0;
}

.hero-nav__links {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex: 1 1 auto;
    flex-wrap: nowrap;
    gap: clamp(12px, 1vw, 24px);
    min-width: 0;
}

.hero-nav__link {
    font-family: var(--font-menu);
    font-size: var(--font-size-menu);
    font-weight: 500;
    line-height: var(--line-height-tight);
    color: var(--text);
    padding: 8px 1px;
    white-space: nowrap;
    border-radius: 0;
    background: transparent;
    border: none;
    position: relative;
    transition: color 200ms ease;
}

.hero-nav__link:hover {
    color: var(--text-strong);
}

.hero-nav__link--active {
    color: var(--text-strong);
}

.hero-nav__link::after {
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

.hero-nav__link:hover::after,
.hero-nav__link--active::after {
    transform: scaleX(1);
}

.hero-nav__actions {
    display: none;
    align-items: center;
    gap: 8px;
    margin-left: 0;
    flex-shrink: 0;
}

.hero-nav__burger {
    display: none;
}

.hero-nav__overlay {
    position: fixed;
    inset: 0;
    background: rgba(16, 13, 10, 0.54);
    backdrop-filter: blur(3px);
    opacity: 0;
    pointer-events: none;
    transition: opacity 200ms ease;
    z-index: 70;
}

.hero-nav__overlay--show {
    opacity: 1;
    pointer-events: auto;
}

.hero-nav__drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: min(88vw, 360px);
    max-height: 100dvh;
    height: 100dvh;
    background: color-mix(in srgb, var(--nav-surface) 86%, transparent);
    border-left: 1px solid rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(18px);
    transform: translateX(100%);
    transition: transform 240ms ease;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 80;
    box-shadow: 0 24px 50px var(--shadow);
    border-radius: 0;
    overflow-y: auto;
}

.hero-nav__drawer--open {
    transform: translateX(0);
}

.hero-nav__drawer-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
}

.hero-nav__drawer-title {
    font-size: clamp(22px, 6vw, 30px);
    color: var(--color-dark-deep);
    font-family: var(--font-brand);
    line-height: 1;
    margin-bottom: 10px;
    letter-spacing: 0.3px;
}

.hero-nav__drawer-close {
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

.hero-nav__drawer-link {
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

.hero-nav__drawer-link:hover {
    color: var(--text-strong);
}

.hero-nav__drawer-link--active {
    color: var(--text-strong);
}

.hero-nav__drawer-link:active {
    transform: scale(0.99);
}

.hero-nav__drawer-cta {
    margin-top: auto;
    width: 100%;
}

.hero__top {
    position: relative;
    background: color-mix(in srgb, var(--card) 70%, #000);
    background-position: center;
    background-size: cover;
    background-repeat: no-repeat;
    height: 420px;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 0 16px;
    box-sizing: border-box;
    overflow: hidden;
}

.hero__top::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, rgba(12, 9, 7, 0.65), rgba(12, 9, 7, 0.1));
}

.hero__top::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(255, 255, 255, 0.2);
    pointer-events: none;
}

.hero__top > * {
    position: relative;
    z-index: 1;
}

.hero__project-title {
    position: absolute;
    top: 56%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 1;
    font-family: var(--font-brand);
    font-size: clamp(44px, 8.4vw, 120px);
    line-height: 0.95;
    letter-spacing: 0.02em;
    color: black;
    text-align: center;
    pointer-events: none;
    width: min(90%, 1100px);
}

.hero__title {
    font-size: 28px;
    color: var(--color-background-light);
    letter-spacing: 0.6px;
    background: rgba(36, 30, 24, 0.45);
    padding: 10px 22px;
    border-radius: 999px;
    text-align: center;
}

.hero__bottom {
    background: var(--color-background-light);
    padding: 72px 32px 32px;
    position: relative;
    box-sizing: border-box;
}

.avatar {
    position: absolute;
    top: 0;
    left: 140px;
    width: 190px;
    height: 190px;
    border-radius: 50%;
    background: var(--card);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    box-shadow: 0 24px 40px var(--shadow);
    border: 3px solid rgba(255, 255, 255, 0.75);
    transform: translateY(-50%);
}

.avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.avatar__placeholder {
    color: var(--muted);
    font-size: var(--font-size-base);
}

.info {
    margin-left: 360px;
    padding-top: 8px;
}

.info__name {
    font-size: 26px;
    color: var(--text-strong);
    margin-bottom: 12px;
    font-weight: 600;
    letter-spacing: 0.2px;
}

.info__row {
    display: grid;
    gap: 14px;
}

.info__about {
    font-size: var(--font-size-small);
    color: var(--muted);
    line-height: var(--line-height-body);
}

.info__status {
    font-size: var(--font-size-caption);
    color: var(--muted);
}

.info__btn {
    justify-self: flex-start;
}

@media (max-width: 1100px) {
    .avatar {
        left: 90px;
        width: 200px;
        height: 200px;
    }

    .info {
        margin-left: 300px;
    }
}

@media (max-width: 1200px) {
    .hero-nav__brand {
        display: none;
    }

    .hero-nav__links {
        display: none;
    }

    .hero-nav__burger {
        display: inline-flex;
    }

    .hero-nav__actions {
        display: inline-flex;
        margin-left: auto;
    }
}

@media (max-width: 768px) {
    .hero-nav__brand {
        display: none;
    }

    .hero-nav {
        width: calc(100% - 24px);
        background: transparent;
        border: none;
        box-shadow: none;
        backdrop-filter: none;
    }

    .hero-nav--stuck {
        background: transparent;
        box-shadow: none;
    }

    .hero-nav__inner {
        padding: 8px var(--container-gutter-mobile);
    }

    .hero-nav__links {
        display: none;
    }

    .hero-nav__burger {
        display: inline-flex;
    }

    .hero-nav__brand {
        font-size: clamp(20px, 7.2vw, 28px);
    }

    .hero__project-title {
        top: 58%;
        font-size: clamp(34px, 10vw, 64px);
        width: min(92%, 560px);
    }

    .hero-nav__drawer {
        width: min(92vw, 340px);
    }
}

@media (max-width: 820px) {
  .hero__bottom {
    padding: 130px 20px 28px;
  }

    .avatar {
        left: 50%;
        transform: translate(-50%, -50%);
    }

    .info {
        margin-left: 0;
        text-align: center;
    }

  .info__btn {
    justify-self: center;
  }
}

@media (max-width: 520px) {
  .avatar {
    left: calc(50% - 54px);
  }

  .hero__top {
    background-position: calc(50% - clamp(8px, 3vw, 16px)) center;
  }

  .hero__project-title {
    top: 60%;
    font-size: clamp(30px, 11vw, 48px);
    letter-spacing: 0.01em;
  }
}
</style>
