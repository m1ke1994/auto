<script setup>
import { computed } from 'vue'
import AppHeader from '../components/AppHeader.vue'
import AppFooter from '../components/AppFooter.vue'
import AppHero from '../components/AppHero.vue'
import AboutMeApp from '../components/AboutMeApp.vue'
import MeditationsSection from '../components/MeditationsSection.vue'
import GallerySection from '../components/GallerySection.vue'
import ReviewsSection from '../components/ReviewsSection.vue'
import SimpleWordsSection from '../components/SimpleWordsSection.vue'
import AppPrices from '../components/AppPrices.vue'
import ContactSection from '../components/ContactSection.vue'

const props = defineProps({ site: { type: Object, required: true }, sections: { type: Array, default: () => [] } })
const byKey = computed(() => Object.fromEntries(props.sections.map((section) => [section.key, section])))
</script>

<template>
  <div class="flex min-h-screen flex-col bg-[#F8F3EA] text-[#24231F]">
    <AppHeader :section="byKey.header" />
    <main class="flex-1">
      <AppHero :section="byKey.hero" />
      <SimpleWordsSection :section="byKey.simple_words" />
      <AboutMeApp :section="byKey.guide" />
      <MeditationsSection :section="byKey.meditations" />
      <GallerySection :section="byKey.gallery" />
      <ReviewsSection :section="byKey.reviews" />
      <AppPrices :section="byKey.services" />
      <ContactSection :section="byKey.contacts" />
    </main>
    <AppFooter :section="byKey.footer" :site="site" />
  </div>
</template>
