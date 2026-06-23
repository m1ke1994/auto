<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { submitLead } from '../composables/useLeadApi'

const props = defineProps({
  service: {
    type: Object,
    default: null,
  },
  serviceType: {
    type: String,
    default: '',
  },
  content: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close'])

const initialForm = () => ({
  name: '',
  phone: '',
  details: '',
})

const form = ref(initialForm())
const errors = ref({})
const isSubmitted = ref(false)
const isSending = ref(false)
const modalRef = ref(null)

let closeTimer = 0
let previousBodyOverflow = ''

const isOpen = computed(() => Boolean(props.service))
const modalTag = computed(() => props.content?.modal_tag || 'Заявка')
const modalTitle = computed(() => props.content?.modal_title || 'Записаться на услугу')
const selectedLabel = computed(() => props.content?.modal_selected_label || 'Выбранный формат')
const priceLabel = computed(() => props.content?.modal_price_label || 'Стоимость')
const durationLabel = computed(() => props.content?.modal_duration_label || 'Длительность')
const nameLabel = computed(() => props.content?.modal_name_label || 'Имя')
const namePlaceholder = computed(() => props.content?.modal_name_placeholder || 'Ваше имя')
const phoneLabel = computed(() => props.content?.modal_phone_label || 'Телефон')
const phonePlaceholder = computed(() => props.content?.modal_phone_placeholder || '+7 999 000-00-00')
const commentLabel = computed(() => props.content?.modal_comment_label || 'Комментарий')
const commentPlaceholder = computed(() => props.content?.modal_comment_placeholder || 'Дата, количество игроков, пожелания')
const submitText = computed(() => props.content?.modal_submit_text || 'Отправить')
const sendingText = computed(() => props.content?.modal_sending_text || 'Отправляем...')
const successText = computed(() => props.content?.modal_success_text || 'Заявка успешно отправлена')

const resetForm = () => {
  form.value = initialForm()
  errors.value = {}
  isSubmitted.value = false
  isSending.value = false
}

const closeModal = () => {
  window.clearTimeout(closeTimer)
  resetForm()
  emit('close')
}

const handleKeydown = (event) => {
  if (event.key === 'Escape' && isOpen.value) {
    closeModal()
  }
}

const addKeydownListener = () => {
  window.addEventListener('keydown', handleKeydown)
}

const removeKeydownListener = () => {
  window.removeEventListener('keydown', handleKeydown)
}

const validatePhone = (value) => {
  const digits = value.replace(/\D/g, '')
  return digits.length >= 10 && digits.length <= 15
}

const validateForm = () => {
  const nextErrors = {}

  if (!form.value.name.trim()) {
    nextErrors.name = 'Введите имя'
  }

  if (!form.value.phone.trim()) {
    nextErrors.phone = 'Введите телефон'
  } else if (!validatePhone(form.value.phone)) {
    nextErrors.phone = 'Проверьте телефон'
  }

  errors.value = nextErrors
  return Object.keys(nextErrors).length === 0
}

const submitForm = async () => {
  if (!validateForm()) return

  isSending.value = true
  errors.value = {}

  try {
    await submitLead({
      section_key: 'services',
      form_name: 'Форма записи на услугу',
      name: form.value.name.trim(),
      phone: form.value.phone.trim(),
      message: form.value.details.trim(),
      service_type: props.serviceType || '',
      service_title: props.service?.title || '',
      payload: {
        service: props.service || null,
      },
    })

    isSubmitted.value = true
    closeTimer = window.setTimeout(() => {
      closeModal()
    }, 1600)
  } catch (error) {
    errors.value.submit = error instanceof Error ? error.message : 'Не удалось отправить заявку'
  } finally {
    isSending.value = false
  }
}

watch(isOpen, async (value) => {
  if (!value) {
    document.body.style.overflow = previousBodyOverflow
    return
  }

  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'

  await nextTick()
  modalRef.value?.focus()
})

onBeforeUnmount(() => {
  window.clearTimeout(closeTimer)
  removeKeydownListener()
  document.body.style.overflow = previousBodyOverflow
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
      @after-enter="addKeydownListener"
      @after-leave="removeKeydownListener"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[999] flex items-center justify-center bg-black/75 p-4 backdrop-blur-md sm:p-6"
        @click.self="closeModal"
      >
        <Transition
          appear
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="translate-y-8 scale-[0.98] opacity-0"
          enter-to-class="translate-y-0 scale-100 opacity-100"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="translate-y-0 scale-100 opacity-100"
          leave-to-class="translate-y-6 scale-[0.98] opacity-0"
        >
          <div
            ref="modalRef"
            tabindex="-1"
            role="dialog"
            aria-modal="true"
            aria-labelledby="service-order-title"
            class="relative box-border max-h-[90vh] w-full max-w-[560px] overflow-hidden rounded-[2rem] border border-white/60 bg-[#FBF7EF] text-[#24231F] shadow-[0_32px_100px_rgba(0,0,0,0.24)] outline-none"
          >
            <button
              type="button"
              class="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-black/10 bg-white/80 text-stone-600 shadow-sm transition duration-300 hover:bg-[#24231F] hover:text-white focus:outline-none focus:ring-2 focus:ring-[#8B7449]/40"
              aria-label="Закрыть окно"
              @click="closeModal"
            >
              <svg
                class="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M6 6l12 12" />
                <path d="M18 6L6 18" />
              </svg>
            </button>

            <div class="box-border max-h-[90vh] w-full min-w-0 overflow-y-auto p-5 sm:p-6 md:p-8">
              <div class="min-w-0 pr-12">
                <p class="mb-2 text-xs font-medium uppercase tracking-[0.24em] text-[#8B7449]/65">
                  {{ modalTag }}
                </p>

                <h2
                  id="service-order-title"
                  class="text-2xl font-semibold leading-tight text-[#24231F] sm:text-3xl"
                >
                  {{ modalTitle }}
                </h2>
              </div>

              <div class="mt-5 box-border w-full min-w-0 rounded-3xl border border-black/10 bg-white p-4 shadow-sm">
                <p class="text-xs font-medium uppercase tracking-[0.2em] text-stone-500">
                  {{ selectedLabel }}
                </p>

                <h3 class="mt-2 min-w-0 text-xl font-semibold leading-7 text-[#24231F]">
                  {{ service.title }}
                </h3>

                <div class="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <div class="box-border min-w-0 rounded-2xl bg-[#FBF7EF] px-4 py-3">
                    <span class="block text-[11px] uppercase tracking-[0.16em] text-stone-500">{{ priceLabel }}</span>
                    <span class="mt-1 block min-w-0 text-sm font-semibold text-[#8B7449]">{{ service.price }}</span>
                  </div>

                  <div class="box-border min-w-0 rounded-2xl bg-[#FBF7EF] px-4 py-3">
                    <span class="block text-[11px] uppercase tracking-[0.16em] text-stone-500">{{ durationLabel }}</span>
                    <span class="mt-1 block min-w-0 text-sm font-semibold text-[#24231F]">{{ service.duration }}</span>
                  </div>
                </div>
              </div>

              <div
                v-if="isSubmitted"
                class="mt-5 box-border w-full min-w-0 rounded-3xl border border-[#8B7449]/20 bg-white p-5 text-center shadow-sm"
              >
                <p class="text-lg font-semibold text-[#24231F]">
                  {{ successText }}
                </p>
              </div>

              <form
                v-else
                class="mt-5 grid w-full min-w-0 grid-cols-1 gap-4"
                @submit.prevent="submitForm"
              >
                <label class="block min-w-0">
                  <span class="mb-1.5 block text-sm font-medium text-[#24231F]">{{ nameLabel }}</span>
                  <input
                    v-model="form.name"
                    type="text"
                    class="block box-border w-full min-w-0 max-w-full rounded-2xl border bg-[#F8F3EA] px-4 py-3 text-sm text-[#24231F] outline-none transition placeholder:text-stone-500 focus:border-[#8B7449] focus:bg-white"
                    :class="errors.name ? 'border-[#8B7449]' : 'border-[#8B7449]/20'"
                    :placeholder="namePlaceholder"
                  >
                  <span
                    v-if="errors.name"
                    class="mt-1.5 block text-sm text-[#8B7449]"
                  >
                    {{ errors.name }}
                  </span>
                </label>

                <label class="block min-w-0">
                  <span class="mb-1.5 block text-sm font-medium text-[#24231F]">{{ phoneLabel }}</span>
                  <input
                    v-model="form.phone"
                    type="tel"
                    class="block box-border w-full min-w-0 max-w-full rounded-2xl border bg-[#F8F3EA] px-4 py-3 text-sm text-[#24231F] outline-none transition placeholder:text-stone-500 focus:border-[#8B7449] focus:bg-white"
                    :class="errors.phone ? 'border-[#8B7449]' : 'border-[#8B7449]/20'"
                    :placeholder="phonePlaceholder"
                  >
                  <span
                    v-if="errors.phone"
                    class="mt-1.5 block text-sm text-[#8B7449]"
                  >
                    {{ errors.phone }}
                  </span>
                </label>

                <label class="block min-w-0">
                  <span class="mb-1.5 block text-sm font-medium text-[#24231F]">{{ commentLabel }}</span>
                  <textarea
                    v-model="form.details"
                    class="block box-border min-h-28 w-full min-w-0 max-w-full resize-none rounded-2xl border border-[#8B7449]/20 bg-[#F8F3EA] px-4 py-3 text-sm text-[#24231F] outline-none transition placeholder:text-stone-500 focus:border-[#8B7449] focus:bg-white"
                    :placeholder="commentPlaceholder"
                  />
                </label>

                <div class="flex min-w-0 flex-col gap-3 sm:flex-row">
                  <button
                    type="submit"
                    class="w-full rounded-full border border-[#24231F]/25 bg-[#24231F] px-6 py-4 text-sm font-semibold uppercase tracking-[0.18em] text-white transition duration-300 hover:-translate-y-0.5 hover:bg-[#8B7449] hover:shadow-[0_18px_45px_rgba(139,116,73,0.18)] disabled:cursor-not-allowed disabled:opacity-70 sm:w-auto sm:flex-1"
                    :disabled="isSending"
                  >
                    {{ isSending ? sendingText : submitText }}
                  </button>
                </div>
                <p v-if="errors.submit" class="text-sm text-[#8B7449]">{{ errors.submit }}</p>
              </form>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

