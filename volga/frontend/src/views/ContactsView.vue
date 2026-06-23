<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import { getSiteSettings } from "../api/siteSettings";
import { buildApiUrl, siteSlug } from "../config/api";

const LEADS_ENDPOINT = buildApiUrl("leads/");
const siteSettings = ref({
  phone: "",
  email: "",
  telegram_url: "",
  telegram_username: "",
  address: "",
});
const submitError = ref("");
const isSubmitting = ref(false);
const success = ref(false);
const successTimerId = ref(null);

const hasAnyContactInfo = computed(() =>
  Boolean(
    siteSettings.value.address ||
      siteSettings.value.phone ||
      siteSettings.value.email ||
      siteSettings.value.telegram_url
  )
);

const phoneHref = computed(() => {
  const safePhone = String(siteSettings.value.phone || "").replace(/[^+\d]/g, "");
  return safePhone ? `tel:${safePhone}` : "";
});

const emailHref = computed(() => {
  const email = String(siteSettings.value.email || "").trim();
  return email ? `mailto:${email}` : "";
});

const clearSuccessTimer = () => {
  if (successTimerId.value) {
    clearTimeout(successTimerId.value);
    successTimerId.value = null;
  }
};

const handleSubmit = async (event) => {
  const form = event.target;
  form.classList.add("is-submitted");
  submitError.value = "";
  success.value = false;
  if (!form.checkValidity() || isSubmitting.value) return;

  const contact = String(form.contact.value || "").trim();
  const payload = {
    site_slug: siteSlug,
    section_key: "contacts",
    form_name: "Contact form",
    name: form.name.value,
    phone: contact,
    email: contact.includes("@") ? contact : "",
    message: form.message.value,
  };

  try {
    isSubmitting.value = true;

    const response = await fetch(LEADS_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let message = "Не удалось отправить заявку. Попробуйте снова.";

      try {
        const errorData = await response.json();
        if (errorData && typeof errorData === "object") {
          const firstError = Object.values(errorData).find((value) => Array.isArray(value) && value.length > 0);
          if (Array.isArray(firstError)) {
            message = String(firstError[0]);
          }
        }
      } catch (parseError) {
        // Ignore parsing errors and keep default message.
      }

      throw new Error(message);
    }

    await response.json();
    form.reset();
    form.classList.remove("is-submitted");
    success.value = true;
    clearSuccessTimer();
    successTimerId.value = setTimeout(() => {
      success.value = false;
      successTimerId.value = null;
    }, 3000);
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : "Не удалось отправить заявку. Попробуйте снова.";
  } finally {
    isSubmitting.value = false;
  }
};

onMounted(async () => {
  try {
    const data = await getSiteSettings();
    siteSettings.value = {
      phone: data?.phone || "",
      email: data?.email || "",
      telegram_url: data?.telegram_url || "",
      telegram_username: data?.telegram_username || "",
      address: data?.address || "",
    };
  } catch (error) {
    console.error("Failed to load site settings for contacts page:", error);
  }
});

onBeforeUnmount(() => {
  clearSuccessTimer();
});
</script>

<template>
  <AppHeader />

  <main class="contacts-page">
    <section class="contacts">
      <div class="contacts__head">
        <h1 class="contacts__title">Как нас найти и связаться</h1>
      </div>

      <div class="contacts__grid">
        <div class="contacts__column">
          <div class="contacts__card glass-card">
            <div v-if="hasAnyContactInfo" class="contacts__list">
              <div v-if="siteSettings.address" class="contacts__item">
                <span class="contacts__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z" />
                    <circle cx="12" cy="10" r="2.5" />
                  </svg>
                </span>
                <div>
                  <p class="contacts__label">Адрес</p>
                  <p class="contacts__value contacts__value--address">{{ siteSettings.address }}</p>
                </div>
              </div>

              <div v-if="siteSettings.phone" class="contacts__item">
                <span class="contacts__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path
                      d="M4.5 6.5c0 6.6 5.4 12 12 12h2.5a1 1 0 0 0 1-1v-3.2a1 1 0 0 0-.76-.97l-3.1-.78a1 1 0 0 0-1.05.43l-1 1.5a10.7 10.7 0 0 1-4.6-4.6l1.5-1a1 1 0 0 0 .43-1.05l-.78-3.1A1 1 0 0 0 9 4.5H5.5a1 1 0 0 0-1 1v1z"
                    />
                  </svg>
                </span>
                <div>
                  <p class="contacts__label">Телефон</p>
                  <p class="contacts__value">
                    <a class="contacts__value-link" :href="phoneHref">
                      {{ siteSettings.phone }}
                    </a>
                  </p>
                </div>
              </div>

              <div v-if="siteSettings.email" class="contacts__item">
                <span class="contacts__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" />
                    <path d="m22 8-10 6L2 8" />
                  </svg>
                </span>
                <div>
                  <p class="contacts__label">Email</p>
                  <p class="contacts__value">
                    <a class="contacts__value-link" :href="emailHref">
                      {{ siteSettings.email }}
                    </a>
                  </p>
                </div>
              </div>

              <div v-if="siteSettings.telegram_url" class="contacts__item">
                <span class="contacts__icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21.5 4.5 3.3 11.5c-.8.3-.8 1.4.1 1.6l4.6 1.3 1.6 4.9c.2.9 1.4 1 1.8.2l2.5-4.2 4.8 3.4c.8.5 1.8.1 2-.8l2.6-11.6c.2-.9-.7-1.6-1.6-1.3z" />
                  </svg>
                </span>
                <div>
                  <p class="contacts__label">Telegram</p>
                  <p class="contacts__value">
                    <a
                      :href="siteSettings.telegram_url"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="telegram-link"
                    >
                      {{ siteSettings.telegram_username || "Telegram" }}
                    </a>
                  </p>
                </div>
              </div>
            </div>
            <p v-else class="contacts__empty">Контактные данные скоро появятся.</p>
          </div>

          <div class="contacts__card contacts__card--map glass-card">
            <iframe
              class="contacts__frame"
              src="https://yandex.com/map-widget/v1/?ll=4.892559%2C52.373059&z=10"
              loading="lazy"
              referrerpolicy="no-referrer-when-downgrade"
              allowfullscreen
              title="Карта — Конаково"
            ></iframe>

            <a class="contacts__cta btn-secondary" href="https://yandex.com/maps/-/CCU05ZxoWA" target="_blank" rel="noopener">
              Открыть в Яндекс Картах
            </a>
          </div>
        </div>

        <form id="contact-form" class="contacts__form glass-card" novalidate @submit.prevent="handleSubmit">
          <label class="contacts__field">
            <span class="contacts__field-label">Имя</span>
            <input class="contacts__input" type="text" name="name" placeholder=" " autocomplete="name" required />
          </label>

          <label class="contacts__field">
            <span class="contacts__field-label">Телефон или Email</span>
            <input class="contacts__input" type="text" name="contact" placeholder=" " autocomplete="email" required />
          </label>

          <label class="contacts__field">
            <span class="contacts__field-label">Сообщение</span>
            <textarea class="contacts__input contacts__input--area" name="message" rows="5" placeholder=" " required></textarea>
          </label>

          <button class="contacts__submit btn-primary" type="submit" :disabled="isSubmitting">Отправить</button>
          <p v-if="success" class="form-success">Отправлено</p>
          <p v-if="submitError">{{ submitError }}</p>
        </form>
      </div>
    </section>
  </main>

  <AppFooter />
</template>

<style scoped>
.contacts-page {
  min-height: 100vh;
}

.contacts {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: calc(var(--header-h, 72px) + 28px) 24px 80px;
  display: grid;
  gap: 20px;
  color: var(--text);
}

.contacts__head {
  display: grid;
  gap: 6px;
}

.contacts__title {
  margin: 0;
  font-size: clamp(30px, 5vw, 46px);
  color: var(--text-strong);
}

.contacts__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.contacts__column {
  display: grid;
  gap: 18px;
}

.contacts__card {
  padding: 18px;
  display: grid;
  gap: 16px;
}

.contacts__list {
  display: grid;
  gap: 14px;
}

.contacts__item {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: 12px;
  align-items: start;
}

.contacts__icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--bg-elevated) 65%, transparent);
  color: var(--text-strong);
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.contacts__label {
  margin: 0 0 4px;
  font-size: var(--font-size-base);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.contacts__value {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--text);
  line-height: 1.5;
}

.contacts__value--address {
  white-space: pre-line;
}

.contacts__value-link {
  color: inherit;
  text-decoration: none;
}

.contacts__value-link:hover,
.contacts__value-link:focus-visible {
  text-decoration: underline;
}

.telegram-link {
  color: inherit;
  text-decoration: none;
}

.telegram-link:hover {
  text-decoration: underline;
}

.contacts__empty {
  margin: 0;
  color: var(--muted);
  font-size: var(--font-size-base);
  line-height: 1.5;
}

.contacts__card--map {
  padding: 14px;
}

.contacts__frame {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 0;
  border-radius: 16px;
}

.contacts__cta {
  justify-self: flex-start;
}

.contacts__form {
  padding: 22px;
  display: grid;
  gap: 16px;
}

.contacts__field {
  display: grid;
  gap: 8px;
}

.contacts__field-label {
  font-size: var(--font-size-base);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.contacts__input {
  width: 100%;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
  background: color-mix(in srgb, var(--bg-elevated) 70%, transparent);
  padding: 12px 14px;
  font-size: var(--font-size-base);
  color: var(--text);
  outline: none;
  transition: border-color 200ms ease, box-shadow 200ms ease, background 200ms ease;
}

.contacts__input--area {
  resize: vertical;
  min-height: 130px;
}

.contacts__input:focus-visible {
  border-color: color-mix(in srgb, var(--primary) 60%, var(--border));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 20%, transparent);
  background: color-mix(in srgb, var(--bg-elevated) 82%, transparent);
}

.contacts__form.is-submitted .contacts__input:invalid {
  border-color: color-mix(in srgb, var(--color-warm-brown) 60%, var(--border));
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-warm-brown) 20%, transparent);
}

.contacts__submit {
  justify-self: flex-start;
}

.form-success {
  color: #2e7d32;
  font-size: var(--font-size-base);
  margin-top: 10px;
}

@media (max-width: 900px) {
  .contacts__grid {
    grid-template-columns: 1fr;
  }

  .contacts__submit {
    width: 100%;
    justify-self: stretch;
  }
}

@media (max-width: 640px) {
  .contacts {
    padding: calc(var(--header-h, 72px) + 20px) 16px 64px;
  }

  .contacts__frame {
    aspect-ratio: 4 / 5;
  }
}
</style>
