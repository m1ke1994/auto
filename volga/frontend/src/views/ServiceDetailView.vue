<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import ServiceBookingForm from "../components/ServiceBookingForm.vue";
import RichText from "../components/ui/RichText.vue";
import { formatPrice, loadServices, useServices } from "../composables/useServices";

const route = useRoute();

const { getServiceByPath, servicesError, servicesLoaded, servicesLoading } = useServices();
const bookingSectionRef = ref(null);
const selectedTariff = ref(null);
const selectedBookingService = ref(null);
const selectedImage = ref("");
const isLightboxOpen = ref(false);

const slugPath = computed(() =>
  String(route.params.slugPath || "").replace(/^\/+|\/+$/g, "")
);

const service = computed(() => getServiceByPath(slugPath.value));
const bookingService = computed(() => selectedBookingService.value || service.value || null);
const hasTariffs = computed(() => Array.isArray(service.value?.tariffs) && service.value.tariffs.length > 0);
const hasChildren = computed(() => Array.isArray(service.value?.children) && service.value.children.length > 0);
const serviceImages = computed(() => {
  const rawImages = Array.isArray(service.value?.images) ? service.value.images : [];
  const normalizedGallery = rawImages
    .map((item, index) => {
      const imageUrl = String(item?.image_url || "").trim();
      if (!imageUrl) return null;
      return {
        id: item?.id ?? `image-${index}`,
        imageUrl,
      };
    })
    .filter(Boolean);

  if (normalizedGallery.length) {
    return normalizedGallery;
  }

  const coverImage = String(service.value?.image || "").trim();
  if (!coverImage) {
    return [];
  }

  return [{ id: `cover-${service.value?.id || "service"}`, imageUrl: coverImage }];
});
const hasGalleryImages = computed(() => serviceImages.value.length > 0);
const hasMultipleGalleryImages = computed(() => serviceImages.value.length > 1);

const chooseTariff = (tariff) => {
  selectedBookingService.value = service.value || null;
  selectedTariff.value = tariff || null;
  bookingSectionRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
};

const openImage = (imageUrl) => {
  if (!hasMultipleGalleryImages.value) return;
  selectedImage.value = imageUrl || "";
  isLightboxOpen.value = Boolean(imageUrl);
};

const closeLightbox = () => {
  isLightboxOpen.value = false;
};

const chooseChildService = (child) => {
  selectedBookingService.value = child || null;
  selectedTariff.value = null;
  bookingSectionRef.value?.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
};

const clearBookingSelection = () => {
  selectedBookingService.value = null;
  selectedTariff.value = null;
};

onMounted(() => {
  loadServices();
});

watch(
  () => route.params.slugPath,
  () => {
    selectedBookingService.value = null;
    selectedTariff.value = null;
    if (!servicesLoaded.value && !servicesLoading.value) {
      loadServices();
    }
  }
);

watch(isLightboxOpen, (isOpen) => {
  if (!isOpen) {
    selectedImage.value = "";
  }
});

watch(
  () => service.value?.id,
  () => {
    closeLightbox();
  }
);
</script>

<template>
  <AppHeader />

  <main class="service-page">
    <section v-if="servicesLoading && !service" class="service-page__inner">
      <div class="service-page__empty glass-card">
        <h1 class="service-page__title">Загрузка...</h1>
      </div>
    </section>

    <section v-else-if="service" class="service-page__inner">
      <header class="service-page__hero">
        <h1 class="service-page__title">{{ service.fullTitle || service.title }}</h1>
        <RichText v-if="service.description" :content="service.description" class="service-page__subtitle" />
      </header>

      <section v-if="service.intro || service.contentSections?.length" class="service-page__section">
        <h2 class="service-page__h2">Описание</h2>
        <RichText v-if="service.intro" :content="service.intro" class="service-page__text" />
        <article
          v-for="(block, index) in service.contentSections || []"
          :key="`${service.id}-content-${index}`"
          class="service-page__content-block"
        >
          <h3 class="service-page__h3">{{ block.title }}</h3>
          <RichText
            :content="Array.isArray(block.paragraphs) ? block.paragraphs : block.text"
            class="service-page__text"
          />
        </article>
      </section>

      <section v-if="hasChildren" class="service-page__section">
        <h2 class="service-page__h2">Подуслуги</h2>
        <div class="service-page__grid">
          <article
            v-for="child in service.children"
            :key="child.id"
            class="service-page__card glass-card"
          >
            <h3 class="service-page__h3">{{ child.title }}</h3>
            <RichText v-if="child.description" :content="child.description" class="service-page__text" />
            <div class="service-page__card-actions">
              <button class="btn-primary" type="button" @click="chooseChildService(child)">
                Выбрать
              </button>
              <router-link class="btn-outline" :to="`/services/${child.path}`">
                Открыть
              </router-link>
            </div>
          </article>
        </div>
      </section>

      <section v-if="hasTariffs" class="service-page__section">
        <h2 class="service-page__h2">Тарифы</h2>
        <div class="service-page__grid">
          <article
            v-for="tariff in service.tariffs"
            :key="tariff.id"
            class="service-page__card glass-card"
          >
            <h3 class="service-page__h3">{{ tariff.title }}</h3>
            <RichText v-if="tariff.description" :content="tariff.description" class="service-page__text" />
            <p v-if="tariff.duration" class="service-page__meta">{{ tariff.duration }}</p>
            <p class="service-page__price">{{ formatPrice(tariff.price) }}</p>
            <button class="btn-primary service-page__choose" type="button" @click="chooseTariff(tariff)">
              {{ tariff.actionLabel || "Выбрать" }}
            </button>
          </article>
        </div>
      </section>

      <section ref="bookingSectionRef" class="service-page__section">
        <ServiceBookingForm
          :service="bookingService"
          :selected-tariff="selectedTariff"
          @update:selected-tariff="selectedTariff = $event"
          @clear-selection="clearBookingSelection"
        />
      </section>

      <section v-if="hasGalleryImages" class="service-page__section">
        <h2 class="service-page__h2">Галерея</h2>
        <div v-if="hasMultipleGalleryImages" class="service-page__images-grid">
          <button
            v-for="image in serviceImages"
            :key="image.id"
            class="service-page__image-btn"
            type="button"
            @click="openImage(image.imageUrl)"
          >
            <img :src="image.imageUrl" :alt="service.title" loading="lazy" decoding="async" />
          </button>
        </div>
        <figure v-else class="service-page__image-single">
          <img :src="serviceImages[0].imageUrl" :alt="service.title" loading="lazy" decoding="async" />
        </figure>
      </section>
    </section>

    <section v-else class="service-page__inner">
      <div class="service-page__empty glass-card">
        <h1 class="service-page__title">Услуга не найдена</h1>
        <p class="service-page__text">
          {{ servicesError || "Откройте раздел услуг на главной и выберите нужный формат." }}
        </p>
        <router-link class="btn-secondary" to="/#services">К услугам</router-link>
      </div>
    </section>
  </main>

  <AppFooter />

  <div v-if="isLightboxOpen && hasMultipleGalleryImages" class="service-page__lightbox-overlay" @click.self="closeLightbox">
    <div class="service-page__lightbox">
      <button class="service-page__lightbox-close" type="button" @click="closeLightbox">×</button>
      <img v-if="selectedImage" :src="selectedImage" :alt="service?.title || 'Изображение услуги'" />
    </div>
  </div>
</template>

<style scoped>
.service-page {
  min-height: 100vh;
  background: var(--bg);
}

.service-page__inner {
  max-width: 980px;
  margin: 0 auto;
  padding: 96px 20px 72px;
  display: grid;
  gap: 20px;
}

.service-page__hero {
  display: grid;
  gap: 12px;
}

.service-page__title {
  margin: 0;
  font-size: clamp(32px, 5vw, 48px);
  line-height: 1.08;
  color: var(--text-strong);
}

.service-page__subtitle {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.service-page__section {
  display: grid;
  gap: 14px;
}

.service-page__h2 {
  margin: 0;
  font-size: clamp(22px, 3.5vw, 30px);
  color: var(--text-strong);
}

.service-page__h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-strong);
}

.service-page__text {
  margin: 0;
  color: var(--text);
  line-height: 1.7;
}

.service-page__content-block {
  display: grid;
  gap: 10px;
}

.service-page__grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.service-page__card {
  padding: 16px;
  display: grid;
  gap: 10px;
}

.service-page__card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.service-page__meta {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--muted);
}

.service-page__price {
  margin: 0;
  font-size: var(--font-size-base);
  font-weight: 700;
  color: var(--color-dark-deep);
}

.service-page__choose {
  justify-self: start;
}

.service-page__images-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.service-page__image-btn {
  border: 0;
  padding: 0;
  cursor: pointer;
  border-radius: 14px;
  overflow: hidden;
  background: color-mix(in srgb, var(--bg-elevated) 80%, transparent);
}

.service-page__image-btn img {
  width: 100%;
  height: 220px;
  display: block;
  object-fit: cover;
  transition: transform 220ms ease;
}

.service-page__image-btn:hover img {
  transform: scale(1.03);
}

.service-page__image-single {
  margin: 0;
  border-radius: 14px;
  overflow: hidden;
  background: color-mix(in srgb, var(--bg-elevated) 80%, transparent);
}

.service-page__image-single img {
  width: 100%;
  max-height: 520px;
  display: block;
  object-fit: cover;
}

.service-page__lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(8, 8, 8, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.service-page__lightbox {
  position: relative;
  width: min(1080px, 96vw);
  max-height: 92vh;
  border-radius: 16px;
  overflow: hidden;
  background: var(--bg);
}

.service-page__lightbox img {
  width: 100%;
  max-height: 92vh;
  object-fit: contain;
  display: block;
}

.service-page__lightbox-close {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--text-strong);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.service-page__empty {
  margin-top: 24px;
  padding: 22px;
  display: grid;
  gap: 12px;
}

@media (max-width: 900px) {
  .service-page__grid {
    grid-template-columns: 1fr;
  }

  .service-page__images-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .service-page__inner {
    padding: 88px 14px 58px;
  }

  .service-page__text,
  .service-page__subtitle {
    font-size: var(--font-size-base);
  }

  .service-page__choose {
    width: 100%;
    justify-content: center;
  }

  .service-page__images-grid {
    grid-template-columns: 1fr;
  }
}
</style>
