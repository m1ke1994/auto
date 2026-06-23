<script setup>
import { computed } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import AppHero from './components/AppHero.vue'
import AboutMeApp from './components/AboutMeApp.vue'
import MeditationsSection from './components/MeditationsSection.vue'
import GallerySection from './components/GallerySection.vue'
import ReviewsSection from './components/ReviewsSection.vue'
import SimpleWordsSection from './components/SimpleWordsSection.vue'
import AppPrices from './components/AppPrices.vue'
import ContactSection from './components/ContactSection.vue'
import { usePublicSiteContent } from './composables/usePublicSiteContent'

const { site, loading, getSection } = usePublicSiteContent()

const headerSection = computed(() => getSection('header'))
const heroSection = computed(() => getSection('hero'))
const simpleWordsSection = computed(() => getSection('simple_words'))
const guideSection = computed(() => getSection('guide'))
const meditationsSection = computed(() => getSection('meditations'))
const gallerySection = computed(() => getSection('gallery'))
const servicesSection = computed(() => getSection('services'))
const reviewsSection = computed(() => getSection('reviews'))
const contactsSection = computed(() => getSection('contacts'))
const footerSection = computed(() => getSection('footer'))
</script>

<template>
  <div class="flex min-h-screen flex-col bg-[#F8F3EA] text-[#24231F]" :aria-busy="loading">
    <AppHeader :section="headerSection" />
    <main class="flex-1">
      <AppHero :section="heroSection" />
      <SimpleWordsSection :section="simpleWordsSection" />
      <AboutMeApp :section="guideSection" />
      <MeditationsSection :section="meditationsSection" />
      <GallerySection :section="gallerySection" />
      <ReviewsSection :section="reviewsSection" />
      <AppPrices :section="servicesSection" />
      <ContactSection :section="contactsSection" />
    </main>
    <AppFooter :section="footerSection" :site="site" />
  </div>
</template>
