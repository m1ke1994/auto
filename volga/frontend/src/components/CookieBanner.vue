<script setup>
import { onMounted, ref } from "vue";
import { loadPublicSite } from "../api/publicSite";

const STORAGE_KEY = "cookies_accepted_v1";
const isVisible = ref(false);

const readAcceptedFlag = () => {
  if (typeof window === "undefined") return true;

  try {
    return window.localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return true;
  }
};

const acceptCookies = () => {
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // Ignore localStorage errors to avoid breaking UI.
    }
  }

  isVisible.value = false;
  loadTrackerScript();
};

onMounted(() => {
  const accepted = readAcceptedFlag();
  isVisible.value = !accepted;
  if (accepted) {
    loadTrackerScript();
  }
});

function loadTrackerScript() {
  loadPublicSite({ enableTracker: true }).catch((error) => {
    console.error("[tracker] failed to load public site config", error);
  });
}
</script>

<template>
  <transition name="cookie-fade">
    <aside v-if="isVisible" class="cookie-banner" role="dialog" aria-live="polite" aria-label="Уведомление о cookies">
      <p class="cookie-banner__text">Мы используем cookies для корректной работы сайта и улучшения пользовательского опыта.</p>
      <button type="button" class="cookie-banner__button btn-primary" @click="acceptCookies">Принять</button>
    </aside>
  </transition>
</template>

<style scoped>
.cookie-banner {
  position: fixed;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  z-index: 120;
  width: min(780px, calc(100vw - 24px));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--border) 80%, transparent);
  background: color-mix(in srgb, var(--nav-surface) 94%, var(--bg));
  box-shadow: 0 16px 30px color-mix(in srgb, var(--shadow) 86%, transparent);
  backdrop-filter: blur(12px);
}

.cookie-banner__text {
  margin: 0;
  color: var(--text);
  font-size: var(--font-size-base);
  line-height: var(--line-height-body);
}

.cookie-banner__button {
  flex-shrink: 0;
}

.cookie-fade-enter-active,
.cookie-fade-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.cookie-fade-enter-from,
.cookie-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}

@media (max-width: 640px) {
  .cookie-banner {
    bottom: 14px;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .cookie-banner__button {
    width: 100%;
  }
}
</style>
