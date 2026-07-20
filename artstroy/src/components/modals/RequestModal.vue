<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRequestModal } from '../../composables/useRequestModal'

const { requestModalState, closeRequestModal } = useRequestModal()

const name = ref('')
const phone = ref('')
const nameError = ref('')
const phoneError = ref('')
const isSubmitting = ref(false)
const isSuccess = ref(false)

const isOpen = computed(() => requestModalState.isOpen)

const resetForm = () => {
  name.value = ''
  phone.value = ''
  nameError.value = ''
  phoneError.value = ''
  isSubmitting.value = false
  isSuccess.value = false
}

const formatPhone = (value) => {
  const digits = value.replace(/\D/g, '').slice(0, 11)

  if (!digits) {
    return ''
  }

  let normalized = digits
  if (normalized[0] === '8') normalized = `7${normalized.slice(1)}`
  if (normalized[0] !== '7') normalized = `7${normalized}`

  const p1 = normalized.slice(1, 4)
  const p2 = normalized.slice(4, 7)
  const p3 = normalized.slice(7, 9)
  const p4 = normalized.slice(9, 11)

  let formatted = '+7'
  if (p1) formatted += ` (${p1}`
  if (p1.length === 3) formatted += ')'
  if (p2) formatted += ` ${p2}`
  if (p3) formatted += `-${p3}`
  if (p4) formatted += `-${p4}`

  return formatted
}

const onPhoneInput = (event) => {
  phone.value = formatPhone(event.target.value)
  if (phoneError.value) {
    phoneError.value = ''
  }
}

const onNameInput = (event) => {
  name.value = event.target.value
  if (nameError.value) {
    nameError.value = ''
  }
}

const closeModal = () => {
  closeRequestModal()
}

const validate = () => {
  let isValid = true

  if (!name.value.trim()) {
    nameError.value = 'Введите имя'
    isValid = false
  }

  const phoneDigits = phone.value.replace(/\D/g, '')
  if (phoneDigits.length < 11) {
    phoneError.value = 'Введите корректный номер'
    isValid = false
  }

  return isValid
}

const submitRequest = () => {
  if (isSubmitting.value || isSuccess.value) return
  if (!validate()) return

  isSubmitting.value = true

  window.setTimeout(() => {
    isSubmitting.value = false
    isSuccess.value = true
    console.log('Request submitted', {
      name: name.value.trim(),
      phone: phone.value,
      source: requestModalState.source,
    })

    window.setTimeout(() => {
      closeModal()
    }, 900)
  }, 700)
}

const onKeydown = (event) => {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal()
  }
}

watch(isOpen, (opened) => {
  document.body.style.overflow = opened ? 'hidden' : ''

  if (opened) {
    resetForm()
  }
})

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="request-fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[120] flex items-center justify-center bg-[#eef2f7]/62 px-4 py-6 backdrop-blur-[4px] sm:px-6"
        @click.self="closeModal"
      >
        <Transition name="request-scale">
          <div
            v-if="isOpen"
            class="w-full max-w-[30rem] rounded-[1.4rem] border border-white/75 bg-white/86 p-5 shadow-[0_20px_56px_rgba(15,23,42,0.18)] backdrop-blur-[12px] sm:p-6"
          >
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-[0.72rem] font-semibold uppercase tracking-[0.16em] text-[#6b7280]">
                  Заявка
                </p>
                <h3 class="mt-2 text-[1.6rem] font-semibold leading-[1.12] tracking-[-0.02em] text-[#111827]">
                  Оставьте контакты
                </h3>
              </div>

              <button
                type="button"
                class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#c5ccd7] bg-white text-[#4b5563] transition duration-200 hover:border-[#a8b3c3] hover:text-[#111827]"
                aria-label="Закрыть"
                @click="closeModal"
              >
                <svg viewBox="0 0 24 24" class="h-4.5 w-4.5" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </button>
            </div>

            <p class="mt-3 text-[0.92rem] leading-[1.6] text-[#5b6472]">
              Мы свяжемся с вами и уточним детали проекта.
            </p>

            <form class="mt-5 space-y-3.5" @submit.prevent="submitRequest">
              <div>
                <label class="mb-1.5 block text-[0.84rem] font-medium text-[#374151]" for="request-name">
                  Имя
                </label>
                <input
                  id="request-name"
                  :value="name"
                  type="text"
                  autocomplete="name"
                  class="h-11 w-full rounded-[0.9rem] border bg-white px-3.5 text-[0.95rem] text-[#111827] outline-none transition duration-200 placeholder:text-[#9aa3af] focus:border-[#64748b] focus:ring-2 focus:ring-[#cbd5e1]"
                  :class="nameError ? 'border-[#d39aa3] focus:ring-[#f2d2d8]' : 'border-[#d0d7e2]'"
                  placeholder="Ваше имя"
                  @input="onNameInput"
                />
                <p v-if="nameError" class="mt-1 text-[0.78rem] text-[#b45363]">
                  {{ nameError }}
                </p>
              </div>

              <div>
                <label class="mb-1.5 block text-[0.84rem] font-medium text-[#374151]" for="request-phone">
                  Номер телефона
                </label>
                <input
                  id="request-phone"
                  :value="phone"
                  type="tel"
                  autocomplete="tel"
                  class="h-11 w-full rounded-[0.9rem] border bg-white px-3.5 text-[0.95rem] text-[#111827] outline-none transition duration-200 placeholder:text-[#9aa3af] focus:border-[#64748b] focus:ring-2 focus:ring-[#cbd5e1]"
                  :class="phoneError ? 'border-[#d39aa3] focus:ring-[#f2d2d8]' : 'border-[#d0d7e2]'"
                  placeholder="+7 (___) ___-__-__"
                  @input="onPhoneInput"
                />
                <p v-if="phoneError" class="mt-1 text-[0.78rem] text-[#b45363]">
                  {{ phoneError }}
                </p>
              </div>

              <button
                type="submit"
                class="mt-1 inline-flex h-11 w-full items-center justify-center rounded-[0.9rem] bg-[#181b24] px-4 text-[0.92rem] font-medium text-white transition duration-200 hover:-translate-y-[1px] hover:bg-black disabled:cursor-not-allowed disabled:opacity-75"
                :disabled="isSubmitting || isSuccess"
              >
                <span v-if="isSubmitting">Отправка...</span>
                <span v-else-if="isSuccess" class="inline-flex items-center gap-2 text-[#d1fae5]">
                  <svg viewBox="0 0 24 24" class="h-4.5 w-4.5 text-[#22c55e]" fill="none" stroke="currentColor" stroke-width="2.4">
                    <path d="m5 13 4 4L19 7" />
                  </svg>
                  Заявка отправлена
                </span>
                <span v-else>Отправить</span>
              </button>
            </form>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.request-fade-enter-active,
.request-fade-leave-active {
  transition: opacity 0.28s ease;
}

.request-fade-enter-from,
.request-fade-leave-to {
  opacity: 0;
}

.request-scale-enter-active,
.request-scale-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.request-scale-enter-from,
.request-scale-leave-to {
  opacity: 0;
  transform: translateY(10px) scale(0.985);
}
</style>
