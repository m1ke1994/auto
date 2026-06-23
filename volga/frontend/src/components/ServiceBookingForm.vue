<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { createServiceRequest } from "../api/serviceRequests";

const props = defineProps({
  service: {
    type: Object,
    default: null,
  },
  selectedTariff: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["update:selectedTariff", "clear-selection"]);

const name = ref("");
const phone = ref("");
const selectedTariffId = ref("");
const isSubmitting = ref(false);
const isSaved = ref(false);
const submitError = ref("");
const successTimerId = ref(null);

const hasSelectedService = computed(() => {
  const title = String(props.service?.title || "").trim();
  const slug = String(props.service?.slug || "").trim();
  return Boolean(title && slug);
});

const tariffs = computed(() =>
  Array.isArray(props.service?.tariffs) ? props.service.tariffs : []
);
const hasTariffs = computed(() => hasSelectedService.value && tariffs.value.length > 0);

const selectedTariffResolved = computed(() => {
  if (!hasTariffs.value || !selectedTariffId.value) return null;
  return (
    tariffs.value.find((tariff) => String(tariff.id) === String(selectedTariffId.value)) ||
    null
  );
});

const canSubmit = computed(() => {
  if (!hasSelectedService.value) return false;
  const hasRequiredFields =
    name.value.trim().length > 0 && phone.value.trim().length > 0;
  if (!hasRequiredFields) return false;
  if (!hasTariffs.value) return true;
  return Boolean(selectedTariffId.value);
});

watch(
  () => props.selectedTariff,
  (tariff) => {
    if (!hasSelectedService.value) {
      selectedTariffId.value = "";
      return;
    }

    if (tariff?.id != null) {
      selectedTariffId.value = String(tariff.id);
      return;
    }
    if (!hasTariffs.value) {
      selectedTariffId.value = "";
    }
  },
  { immediate: true }
);

watch(
  () => props.service?.id,
  () => {
    name.value = "";
    phone.value = "";
    selectedTariffId.value = "";
    isSaved.value = false;
    submitError.value = "";
    emit("update:selectedTariff", null);
  }
);

watch(selectedTariffId, (value) => {
  if (!hasSelectedService.value || !hasTariffs.value) {
    emit("update:selectedTariff", null);
    return;
  }

  const tariff =
    tariffs.value.find((item) => String(item.id) === String(value || "")) || null;
  emit("update:selectedTariff", tariff);
});

const clearSuccessTimer = () => {
  if (successTimerId.value) {
    clearTimeout(successTimerId.value);
    successTimerId.value = null;
  }
};

const resetForm = () => {
  name.value = "";
  phone.value = "";
  selectedTariffId.value = "";
  isSaved.value = false;
  submitError.value = "";
  emit("update:selectedTariff", null);
};

const clearSelection = () => {
  clearSuccessTimer();
  resetForm();
  emit("clear-selection");
};

const handleSubmit = async () => {
  if (!canSubmit.value || isSubmitting.value) return;

  submitError.value = "";
  const tariff = selectedTariffResolved.value;

  try {
    isSubmitting.value = true;
    await createServiceRequest({
      name: name.value.trim(),
      contact: phone.value.trim(),
      service_slug: String(props.service?.slug || "").trim(),
      service_title: String(props.service?.title || "").trim(),
      tariff_id: tariff?.id ?? null,
      tariff_title: tariff?.title || "",
      message: tariff?.title ? `Выбран тариф: ${tariff.title}` : "",
    });

    clearSelection();
    isSaved.value = true;
    clearSuccessTimer();
    successTimerId.value = setTimeout(() => {
      isSaved.value = false;
      successTimerId.value = null;
    }, 3000);
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : "Не удалось отправить заявку. Попробуйте снова.";
  } finally {
    isSubmitting.value = false;
  }
};

onBeforeUnmount(() => {
  clearSuccessTimer();
});
</script>

<template>
  <section class="service-booking glass-card">
    <h2 class="service-booking__title">Запись на услугу</h2>
    <p class="service-booking__subtitle">
      Оставьте контакт, и мы свяжемся с вами для подтверждения записи.
    </p>

    <form class="service-booking__form" @submit.prevent="handleSubmit" novalidate>
      <label class="service-booking__field">
        <span class="service-booking__label">Имя</span>
        <input
          v-model.trim="name"
          class="service-booking__input"
          type="text"
          name="name"
          autocomplete="name"
          required
        />
      </label>

      <label class="service-booking__field">
        <span class="service-booking__label">Телефон</span>
        <input
          v-model.trim="phone"
          class="service-booking__input"
          type="tel"
          name="phone"
          autocomplete="tel"
          required
        />
      </label>

      <label v-if="hasTariffs" class="service-booking__field">
        <span class="service-booking__label">Тариф</span>
        <select v-model="selectedTariffId" class="service-booking__input" name="tariff" required>
          <option value="" disabled>Выберите тариф</option>
          <option v-for="tariff in tariffs" :key="tariff.id" :value="String(tariff.id)">
            {{ tariff.title }}
          </option>
        </select>
      </label>

      <div class="service-booking__actions">
        <button class="btn-primary service-booking__submit" type="submit" :disabled="!canSubmit || isSubmitting">
          Отправить
        </button>
        <button
          class="btn-outline service-booking__clear"
          type="button"
          :disabled="isSubmitting"
          @click="clearSelection"
        >
          Очистить
        </button>
      </div>
      <p v-if="isSaved" class="service-booking__success" style="color: #2e7d32;">Отправлено</p>
      <p v-if="submitError" class="service-booking__success">{{ submitError }}</p>
    </form>
  </section>

</template>

<style scoped>
.service-booking {
  padding: 20px;
  display: grid;
  gap: 12px;
}

.service-booking__title {
  margin: 0;
  font-size: clamp(22px, 3.5vw, 30px);
  color: var(--text-strong);
}

.service-booking__subtitle {
  margin: 0;
  color: var(--muted);
  font-size: var(--font-size-base);
  line-height: 1.6;
}

.service-booking__form {
  display: grid;
  gap: 12px;
}

.service-booking__field {
  display: grid;
  gap: 6px;
}

.service-booking__label {
  font-size: var(--font-size-base);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.service-booking__input {
  width: 100%;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--bg-elevated) 70%, transparent);
  padding: 11px 12px;
  font-size: var(--font-size-base);
  color: var(--text);
  outline: none;
}

.service-booking__input:focus-visible {
  border-color: color-mix(in srgb, var(--primary) 60%, var(--border));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 20%, transparent);
}

.service-booking__submit[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

.service-booking__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.service-booking__success {
  margin: 0;
  color: var(--text);
  line-height: 1.6;
}

@media (max-width: 720px) {
  .service-booking__submit {
    width: 100%;
    justify-content: center;
  }
}
</style>
