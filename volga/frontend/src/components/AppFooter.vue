<template>
  <footer class="footer">
    <div class="footer__shell">
      <div class="footer__inner">
        <div class="footer__top">
          <div class="footer__brand">
            <div class="footer__logo">Новое Конаково</div>
            <p class="footer__tagline">Тихий отдых • Природа • Внимание к деталям</p>
          </div>

          <div v-if="hasContacts" class="footer__contacts">
            <div v-if="siteSettings.phone" class="footer__contact-card">
              <span class="footer__label">Телефон</span>
              <a class="footer__contact-link" :href="phoneHref">
                {{ siteSettings.phone }}
              </a>
            </div>

            <div v-if="siteSettings.email" class="footer__contact-card">
              <span class="footer__label">E-mail</span>
              <a class="footer__contact-link" :href="emailHref">
                {{ siteSettings.email }}
              </a>
            </div>

            <div v-if="siteSettings.telegram_url" class="footer__contact-card">
              <span class="footer__label">Telegram</span>
              <a
                class="footer__contact-link"
                :href="siteSettings.telegram_url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ siteSettings.telegram_username || "Telegram" }}
              </a>
            </div>
          </div>
        </div>

        <div class="footer__bottom">
          <span class="footer__copyright">
            © {{ year }} New Konakovo. Все права защищены.
          </span>

          <div class="footer__bottom-links">
            <router-link class="footer__bottom-link" to="/privacy">Политика</router-link>
            <router-link class="footer__bottom-link" to="/terms">Условия</router-link>

            <button class="footer__to-top" type="button" @click="scrollToTop" aria-label="Наверх">
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { getSiteSettings } from "../api/siteSettings"

const year = new Date().getFullYear()

const siteSettings = ref({
  phone: "",
  email: "",
  telegram_url: "",
  telegram_username: "",
  address: "",
})

const hasContacts = computed(() =>
  Boolean(
    siteSettings.value.phone ||
      siteSettings.value.email ||
      siteSettings.value.telegram_url
  )
)

const phoneHref = computed(() => {
  const safePhone = String(siteSettings.value.phone || "").replace(/[^+\d]/g, "")
  return safePhone ? `tel:${safePhone}` : ""
})

const emailHref = computed(() => {
  const email = String(siteSettings.value.email || "").trim()
  return email ? `mailto:${email}` : ""
})

onMounted(async () => {
  try {
    const data = await getSiteSettings()
    siteSettings.value = {
      phone: data?.phone || "",
      email: data?.email || "",
      telegram_url: data?.telegram_url || "",
      telegram_username: data?.telegram_username || "",
      address: data?.address || "",
    }
  } catch (error) {
    console.error("Не удалось загрузить настройки сайта для футера:", error)
  }
})

const scrollToTop = () => {
  if (typeof window === "undefined") return
  window.scrollTo({ top: 0, left: 0, behavior: "smooth" })
}
</script>

<style scoped>
.footer {
  width: 100%;
  padding: clamp(24px, 4vw, 56px) clamp(12px, 2vw, 20px) clamp(20px, 3vw, 32px);
  background: var(--bg);
  color: var(--text);
  box-sizing: border-box;
}

.footer__shell {
  width: 100%;
  max-width: min(1320px, calc(100vw - 24px));
  margin: 0 auto;
  border: 1px solid color-mix(in srgb, var(--border) 72%, transparent);
  border-radius: clamp(20px, 2.4vw, 28px);
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.14), transparent 32%),
    radial-gradient(circle at right top, rgba(255, 255, 255, 0.08), transparent 26%),
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--card) 88%, transparent),
      color-mix(in srgb, var(--bg) 32%, transparent),
      color-mix(in srgb, var(--card) 76%, transparent)
    );
  box-shadow: 0 -14px 34px color-mix(in srgb, var(--shadow) 72%, transparent);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.footer__inner {
  position: relative;
  z-index: 1;
  padding: clamp(22px, 3vw, 34px);
  display: grid;
  gap: clamp(20px, 2.6vw, 30px);
}

.footer__top {
  display: grid;
  grid-template-columns: minmax(260px, 1.1fr) minmax(280px, 1fr);
  gap: clamp(20px, 3vw, 36px);
  align-items: start;
}

.footer__brand {
  display: grid;
  gap: 10px;
  align-content: start;
  min-width: 0;
}

.footer__logo {
  font-size: clamp(24px, 3vw, 34px);
  line-height: 1.1;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--text-strong);
  word-break: break-word;
}

.footer__tagline {
  margin: 0;
  max-width: 520px;
  color: var(--muted);
  font-size: clamp(15px, 1.5vw, var(--font-size-menu));
  line-height: 1.6;
}

.footer__contacts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(10px, 1.4vw, 16px);
  min-width: 0;
}

.footer__contact-card {
  min-width: 0;
  display: grid;
  gap: 6px;
  padding: clamp(12px, 1.8vw, 16px);
  backdrop-filter: blur(10px);
}

.footer__label {
  font-size: clamp(11px, 1vw, var(--font-size-caption));
  line-height: 1.2;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.footer__contact-link {
  color: var(--text);
  text-decoration: none;
  font-size: clamp(14px, 1.2vw, var(--font-size-menu));
  line-height: 1.5;
  overflow-wrap: anywhere;
  transition: color 180ms ease, opacity 180ms ease;
}

.footer__contact-link:hover,
.footer__contact-link:focus-visible {
  color: var(--text-strong);
  opacity: 0.9;
  text-decoration: underline;
}

.footer__bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: clamp(18px, 2vw, 22px);
  border-top: 1px solid color-mix(in srgb, var(--border) 55%, transparent);
}

.footer__copyright {
  color: var(--muted);
  font-size: clamp(12px, 1vw, var(--font-size-caption));
  line-height: 1.5;
}

.footer__bottom-links {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 14px;
}

.footer__bottom-link {
  position: relative;
  color: var(--muted);
  text-decoration: none;
  font-size: clamp(12px, 1vw, var(--font-size-caption));
  line-height: 1.4;
  transition: color 180ms ease;
}

.footer__bottom-link::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -3px;
  height: 1px;
  background: color-mix(in srgb, var(--primary) 75%, transparent);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 180ms ease;
}

.footer__bottom-link:hover,
.footer__bottom-link:focus-visible {
  color: var(--text);
}

.footer__bottom-link:hover::after,
.footer__bottom-link:focus-visible::after {
  transform: scaleX(1);
}

.footer__to-top {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--card) 78%, transparent);
  color: var(--text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background 180ms ease;
}

.footer__to-top:hover,
.footer__to-top:focus-visible {
  transform: translateY(-2px);
  background: color-mix(in srgb, var(--card) 88%, transparent);
  box-shadow: 0 10px 20px color-mix(in srgb, var(--shadow) 65%, transparent);
}

@media (max-width: 1100px) {
  .footer__top {
    grid-template-columns: 1fr;
  }

  .footer__contacts {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .footer__contacts {
    grid-template-columns: 1fr;
  }

  .footer__bottom {
    flex-direction: column;
    align-items: flex-start;
  }

  .footer__bottom-links {
    justify-content: flex-start;
  }
}

@media (max-width: 480px) {
  .footer {
    padding: 20px 10px 16px;
  }

  .footer__inner {
    padding: 18px 14px;
  }

  .footer__logo {
    font-size: 24px;
  }

  .footer__tagline {
    font-size: 14px;
  }

  .footer__contact-card {
    padding: 12px;
    border-radius: 16px;
  }

  .footer__bottom-links {
    gap: 12px;
  }
}
</style>
