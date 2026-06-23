<template>
  <div class="scenario">
    <div class="scenario__layout">
      <section class="scenario__main">
        <h2 class="scenario__title">Соберите сценарий дня</h2>

        <div class="services">
          <div v-for="service in servicesWithTariffs" :key="service.id" class="service">
            <button class="service__header" @click="toggleService(service.id)">
              <span class="service__name">
                {{ service.title }}
              </span>

              <span class="service__toggle">
                {{ openServiceId === service.id ? "−" : "+" }}
              </span>
            </button>

            <div v-if="openServiceId === service.id" class="service__body">
              <div
                v-for="tariff in service.tariffs"
                :key="tariff.id"
                class="tariff"
                :class="{ active: selectedTariffIds.includes(tariff.id) }"
              >
                <div class="tariff__row">
                  <span class="tariff__title">
                    {{ tariff.title }}
                  </span>

                  <span class="tariff__price">
                    {{ formatPrice(tariff.price) }}
                  </span>

                  <button
                    class="tariff__btn"
                    :class="{ active: selectedTariffIds.includes(tariff.id) }"
                    @click="toggleTariff(tariff.id)"
                  >
                    {{ selectedTariffIds.includes(tariff.id) ? "✓" : "+" }}
                  </button>
                </div>

                <RichText :content="tariff.description" class="tariff__desc" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <aside class="scenario__aside">
        <div class="panel">
          <input type="text" v-model="name" placeholder="Имя" />

          <input
            type="email"
            v-model="email"
            placeholder="Email"
          />

          <input type="date" v-model="date" placeholder="Выберите дату" />
          <input
            type="number"
            min="1"
            max="10"
            v-model.number="guests"
            placeholder="Количество гостей"
          />
          <textarea rows="3" v-model="comment" placeholder="Комментарий"></textarea>

          <div class="summary">
            <div class="summary__row">
              <span>Итого</span>
              <strong>{{ formatPrice(total) }}</strong>
            </div>

            <div v-for="t in selectedTariffs" :key="t.tariffId" class="summary__item">
              {{ t.serviceTitle }} — {{ t.title }}
            </div>
          </div>

          <button class="btn-primary" :disabled="isSubmitting" @click="handleConfirm">
            Согласовать
          </button>
          <p v-if="success" class="form-success">Отправлено</p>
          <p v-if="submitError">{{ submitError }}</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { createDayScenario } from "../api/dayScenarios";
import { formatPrice, loadServices, useServices } from "../composables/useServices";
import RichText from "./ui/RichText.vue";

const { servicesWithTariffs } = useServices();

const selectedTariffIds = ref([]);
const openServiceId = ref(null);
const name = ref("");
const email = ref("");
const date = ref("");
const guests = ref("");
const comment = ref("");
const isSubmitting = ref(false);
const success = ref(false);
const submitError = ref("");
const successTimerId = ref(null);

const clearSuccessTimer = () => {
  if (successTimerId.value) {
    clearTimeout(successTimerId.value);
    successTimerId.value = null;
  }
};

onMounted(() => {
  loadServices();
});

const toggleService = (id) => {
  openServiceId.value = openServiceId.value === id ? null : id;
};

const toggleTariff = (id) => {
  selectedTariffIds.value = selectedTariffIds.value.includes(id)
    ? selectedTariffIds.value.filter((item) => item !== id)
    : [...selectedTariffIds.value, id];
};

const selectedTariffs = computed(() =>
  servicesWithTariffs.value.flatMap((service) =>
    service.tariffs
      .filter((tariff) => selectedTariffIds.value.includes(tariff.id))
      .map((tariff) => ({
        tariffId: tariff.id,
        title: tariff.title,
        price: tariff.price,
        serviceTitle: service.title,
      }))
  )
);

const total = computed(() => selectedTariffs.value.reduce((sum, tariff) => sum + tariff.price, 0));

const resetScenarioForm = () => {
  selectedTariffIds.value = [];
  name.value = "";
  email.value = "";
  date.value = "";
  guests.value = "";
  comment.value = "";
};

const handleConfirm = async () => {
  if (isSubmitting.value) return;
  submitError.value = "";
  success.value = false;

  const trimmedName = name.value.trim();
  const trimmedEmail = email.value.trim();
  const guestsCount = Number(guests.value);
  const selectedItems = selectedTariffs.value.map((tariff) => ({
    title: `${tariff.serviceTitle} - ${tariff.title}`,
    price: tariff.price,
    quantity: 1,
  }));

  if (!trimmedName || !trimmedEmail || !date.value || !Number.isFinite(guestsCount) || guestsCount < 1) {
    submitError.value = "Заполните имя, email, дату и количество гостей.";
    return;
  }

  if (!selectedItems.length) {
    submitError.value = "Выберите хотя бы одну программу.";
    return;
  }

  try {
    isSubmitting.value = true;
    await createDayScenario({
      name: trimmedName,
      email: trimmedEmail,
      date: date.value,
      guests_count: guestsCount,
      comment: comment.value.trim(),
      total_price: total.value,
      items: selectedItems,
    });

    resetScenarioForm();
    success.value = true;
    clearSuccessTimer();
    successTimerId.value = setTimeout(() => {
      success.value = false;
      successTimerId.value = null;
    }, 3000);
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : "Не удалось отправить сценарий. Попробуйте снова.";
  } finally {
    isSubmitting.value = false;
  }
};

onBeforeUnmount(() => {
  clearSuccessTimer();
});
</script>

<style scoped>
.scenario {
  padding: 32px 0;
}

.scenario__layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 40px;
}

.scenario__title {
  margin-bottom: 20px;
  font-size: 20px;
}

.service {
  border-bottom: 1px solid var(--border);
}

.service__header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border: none;
  background: none;
  cursor: pointer;
  font-weight: 600;
}

.service__name {
  font-size: var(--font-size-base);
}

.service__toggle {
  font-size: 18px;
}

.service__body {
  padding-bottom: 12px;
}

.tariff {
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.tariff__row {
  display: grid;
  grid-template-columns: 1fr 130px 44px;
  align-items: center;
  gap: 10px;
}

.tariff__title {
  font-size: var(--font-size-base);
  font-weight: 600;
}

.tariff__price {
  text-align: right;
  font-size: var(--font-size-base);
  font-weight: 600;
}

.tariff__btn {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: transparent;
  cursor: pointer;
  font-size: var(--font-size-base);
  line-height: 1;
}

.tariff__btn.active {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--color-dark-deep);
}

.tariff__desc {
  font-size: var(--font-size-base);
  color: var(--muted);
  margin-top: 4px;
}

.panel {
  position: sticky;
  top: 90px;
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--card);
}

.panel input,
.panel textarea {
  padding: 10px;
  font-size: var(--font-size-base);
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-elevated);
}

.summary__row {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-base);
  margin-bottom: 6px;
}

.summary__item {
  font-size: var(--font-size-base);
  color: var(--muted);
}

.form-success {
  color: #2e7d32;
  font-size: var(--font-size-base);
  margin-top: 10px;
}

@media (max-width: 980px) {
  .scenario__layout {
    grid-template-columns: 1fr;
  }

  .panel {
    position: static;
  }
}
</style>
