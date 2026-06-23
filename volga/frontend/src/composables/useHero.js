import { ref } from "vue"

import { getSectionContent, toPublicMediaUrl } from "../api/publicSite"

const hero = ref(null)
const loadingHero = ref(false)
const heroError = ref("")

export const loadHero = async () => {
  loadingHero.value = true
  heroError.value = ""

  try {
    const payload = await getSectionContent("hero")
    hero.value = {
      id: payload?.id ?? null,
      title: String(payload?.title || ""),
      description: String(payload?.description || ""),
      background_image: toPublicMediaUrl(payload?.background_image),
      avatar: toPublicMediaUrl(payload?.avatar),
    }
  } catch (error) {
    console.error("[hero] failed to load", error)
    hero.value = null
    heroError.value = "Не удалось загрузить Hero-данные"
  } finally {
    loadingHero.value = false
  }
}

export const useHero = () => ({
  hero,
  loadingHero,
  heroError,
  loadHero,
})
