<script setup>
import { computed, onMounted, ref } from "vue"
import { RouterLink } from "vue-router"
import { loadPublicSite } from "../api/publicSite"

const CONSENT_STORAGE_KEY = "nk_cookie_consent"
const CONSENT_COOKIE_KEY = "nk_cookie_consent"
const CONSENT_COOKIE_DAYS = 180

const consentValue = ref(null)

const isVisible = computed(() => consentValue.value !== "accepted" && consentValue.value !== "rejected")

const setCookie = (name, value, days) => {
  if (typeof document === "undefined") return

  const expires = new Date()
  expires.setDate(expires.getDate() + days)
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`
}

const getCookie = (name) => {
  if (typeof document === "undefined") return ""

  const cookieName = `${name}=`
  const cookies = document.cookie.split(";")
  for (const cookiePart of cookies) {
    const value = cookiePart.trim()
    if (value.startsWith(cookieName)) {
      return decodeURIComponent(value.slice(cookieName.length))
    }
  }
  return ""
}

const loadTrackerScript = () => {
  loadPublicSite({ enableTracker: true }).catch((error) => {
    console.error("[tracker] failed to load public site config", error)
  })
}

const persistConsent = (value) => {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, value)
  }
  setCookie(CONSENT_COOKIE_KEY, value, CONSENT_COOKIE_DAYS)
  consentValue.value = value
}

const acceptCookies = () => {
  persistConsent("accepted")
  loadTrackerScript()
}

const rejectCookies = () => {
  persistConsent("rejected")
}

onMounted(() => {
  const storageValue =
    typeof window !== "undefined" ? window.localStorage.getItem(CONSENT_STORAGE_KEY) || "" : ""
  const cookieValue = getCookie(CONSENT_COOKIE_KEY)
  const resolvedValue = storageValue || cookieValue

  if (resolvedValue === "accepted" || resolvedValue === "rejected") {
    consentValue.value = resolvedValue
    if (resolvedValue === "accepted") {
      loadTrackerScript()
    }
    return
  }

  consentValue.value = null
})
</script>

<template>
  <div v-if="isVisible" class="cookie-consent" role="dialog" aria-live="polite" aria-label="Уведомление о cookies">
    <div class="cookie-consent__content">
      <p class="cookie-consent__text">
        Мы используем cookie для стабильной работы сайта и аналитики. Нажимая «Принять», вы соглашаетесь на
        использование cookie.
        <RouterLink class="cookie-consent__link" to="/privacy">Подробнее в политике конфиденциальности</RouterLink>.
      </p>

      <div class="cookie-consent__actions">
        <button class="btn-primary cookie-consent__button" type="button" @click="acceptCookies">Принять</button>
        <button class="btn-outline cookie-consent__button" type="button" @click="rejectCookies">Отклонить</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cookie-consent {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: 16px;
  z-index: 120;
}

.cookie-consent__content {
  max-width: 960px;
  margin: 0 auto;
  border-radius: 16px;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--card) 92%, transparent);
  box-shadow: 0 14px 30px color-mix(in srgb, var(--shadow) 80%, transparent);
  padding: 14px 16px;
  display: grid;
  gap: 12px;
  backdrop-filter: blur(12px);
}

.cookie-consent__text {
  margin: 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
}

.cookie-consent__link {
  text-decoration: underline;
  text-underline-offset: 2px;
}

.cookie-consent__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.cookie-consent__button {
  min-width: 122px;
}

@media (max-width: 680px) {
  .cookie-consent {
    left: 12px;
    right: 12px;
    bottom: 12px;
  }

  .cookie-consent__content {
    padding: 12px;
  }

  .cookie-consent__actions {
    justify-content: stretch;
  }

  .cookie-consent__button {
    width: 100%;
  }
}
</style>
