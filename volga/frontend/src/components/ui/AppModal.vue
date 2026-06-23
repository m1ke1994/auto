<template>
  <Teleport to="body">
    <transition name="app-modal-fade">
      <div v-if="modelValue" class="app-modal" @click.self="close">
        <div
          ref="panelRef"
          class="app-modal__panel"
          :style="panelStyle"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          @keydown="onKeydown"
        >
          <header class="app-modal__header">
            <h2 :id="titleId" class="app-modal__title">{{ title }}</h2>
            <button
              ref="closeButtonRef"
              class="app-modal__close"
              type="button"
              aria-label="Закрыть окно"
              @click="close"
            >
              ×
            </button>
          </header>
          <div class="app-modal__body">
            <slot />
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue"

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "" },
  panelWidth: { type: String, default: "min(860px, 92vw)" },
  panelMaxHeight: { type: String, default: "86vh" },
})

const emit = defineEmits(["update:modelValue"])

const closeButtonRef = ref(null)
const panelRef = ref(null)
const titleId = `app-modal-title-${Math.random().toString(36).slice(2, 9)}`
const previousOverflow = ref("")

const close = () => {
  emit("update:modelValue", false)
}

const panelStyle = computed(() => ({
  width: props.panelWidth,
  maxHeight: props.panelMaxHeight,
}))

const focusFirst = async () => {
  await nextTick()
  if (closeButtonRef.value) {
    closeButtonRef.value.focus()
  }
}

const onEsc = (event) => {
  if (event.key === "Escape") {
    close()
  }
}

const onKeydown = (event) => {
  if (event.key !== "Tab") return

  const focusables = panelRef.value?.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  if (!focusables || focusables.length === 0) {
    event.preventDefault()
    return
  }

  const first = focusables[0]
  const last = focusables[focusables.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
    return
  }

  if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(
  () => props.modelValue,
  async (value) => {
    if (value) {
      previousOverflow.value = document.documentElement.style.overflow
      document.documentElement.style.overflow = "hidden"
      await focusFirst()
      document.addEventListener("keydown", onEsc)
    } else {
      document.documentElement.style.overflow = previousOverflow.value
      document.removeEventListener("keydown", onEsc)
    }
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  document.documentElement.style.overflow = previousOverflow.value
  document.removeEventListener("keydown", onEsc)
})
</script>

<style scoped>
.app-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(10, 10, 10, 0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 50;
}

.app-modal__panel {
  width: min(860px, 92vw);
  max-height: 86vh;
  overflow: auto;
  border-radius: 24px;
  background: var(--card);
  border: 1px solid var(--border);
  box-shadow:
    0 28px 80px var(--shadow),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  padding: 24px 24px 28px;
  transform: translateY(10px);
}

.app-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.app-modal__title {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
  color: var(--text-strong);
}

.app-modal__close {
  border: 1px solid var(--border);
  background: var(--bg-elevated);
  color: var(--text-strong);
  width: 36px;
  height: 36px;
  border-radius: 999px;
  font-size: 22px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease;
  box-shadow: 0 8px 20px var(--shadow);
}

.app-modal__close:hover {
  transform: translateY(-1px);
  background: var(--bg);
}

.app-modal__body {
  margin-top: 16px;
}

.app-modal-fade-enter-active,
.app-modal-fade-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.app-modal-fade-enter-from,
.app-modal-fade-leave-to {
  opacity: 0;
}

.app-modal-fade-enter-from .app-modal__panel,
.app-modal-fade-leave-to .app-modal__panel {
  transform: translateY(24px);
}

@media (max-width: 640px) {
  .app-modal {
    padding: 16px;
  }

  .app-modal__panel {
    padding: 20px;
    border-radius: 20px;
  }

  .app-modal__title {
    font-size: 20px;
  }
}
</style>
