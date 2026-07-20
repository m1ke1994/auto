import { reactive, readonly } from 'vue'

const requestModalState = reactive({
  isOpen: false,
  source: 'unknown',
})

const openRequestModal = (source = 'unknown') => {
  requestModalState.source = source
  requestModalState.isOpen = true
}

const closeRequestModal = () => {
  requestModalState.isOpen = false
}

export const useRequestModal = () => ({
  requestModalState: readonly(requestModalState),
  openRequestModal,
  closeRequestModal,
})
