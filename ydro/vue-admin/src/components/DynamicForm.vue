<script setup>
import { computed } from 'vue'

import DynamicField from './DynamicField.vue'
import { groupFields } from '../utils/formPresentation'

const props = defineProps({
  schema: {
    type: Object,
    default: () => ({}),
  },
  modelValue: {
    type: Object,
    default: () => ({}),
  },
  uploadContext: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue'])
const fieldGroups = computed(() => groupFields(props.schema?.fields || []))

function updateField(key, value) {
  emit('update:modelValue', {
    ...(typeof props.modelValue === 'object' && props.modelValue ? props.modelValue : {}),
    [key]: value,
  })
}
</script>

<template>
  <div class="space-y-4">
    <section
      v-for="group in fieldGroups"
      :key="group.id"
      class="rounded-2xl border border-brand-100 bg-white/92 p-4 shadow-soft"
    >
      <div class="mb-4 border-b border-brand-100 pb-3">
        <h3 class="text-sm font-semibold text-[#17223B]">{{ group.title }}</h3>
        <p class="mt-1 text-xs leading-5 text-slate-500">{{ group.description }}</p>
      </div>

      <div class="grid gap-4" :class="group.id === 'parameters' ? 'sm:grid-cols-2 xl:grid-cols-3' : ''">
        <DynamicField
          v-for="field in group.fields"
          :key="field.key"
          :field="field"
          :model-value="modelValue?.[field.key]"
          :upload-context="uploadContext"
          :path-prefix="field.key"
          @update:model-value="(value) => updateField(field.key, value)"
        />
      </div>
    </section>
  </div>
</template>
