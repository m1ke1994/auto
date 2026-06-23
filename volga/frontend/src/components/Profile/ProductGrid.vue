<template>
  <div v-if="servicesLoading && !cards.length" class="services-state glass-card" v-reveal>
    <h3 class="services-state__title">Загружаем услуги...</h3>
  </div>

  <div v-else-if="!cards.length" class="services-state glass-card" v-reveal>
    <h3 class="services-state__title">Услуги пока недоступны</h3>
    <p class="services-state__text">
      {{ servicesError || "Проверьте настройки API и наличие активных услуг в базе." }}
    </p>
  </div>

  <div v-else class="services">
    <article v-for="card in cards" :key="card.id" class="card" v-reveal>
      <div class="media">
        <img
          :src="card.image"
          :alt="card.title"
          loading="lazy"
          decoding="async"
          fetchpriority="low"
          width="800"
          height="450"
          class="media__img img-lazy"
          @load="markImageLoaded"
        />
        <div class="media-overlay"></div>
      </div>

      <div class="content">
        <header class="top">
          <h3 class="title">{{ card.title }}</h3>

          <div class="meta">
            <span v-if="card.duration" class="chip">{{ card.duration }}</span>
            
            <span v-if="card.priceLabel" class="price">{{ card.priceLabel }}</span>
          </div>
        </header>

        <RichText v-if="card.desc" :content="card.desc" class="description" />

        <footer class="bottom">
          <router-link class="btn-outline product-grid__more" :to="card.detailsPath">
            {{ card.detailsLabel }}
            <span class="arrow">→</span>
          </router-link>
        </footer>
      </div>
    </article>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import {
  findMinTariffPrice,
  formatPrice,
  loadServices,
  useServices,
} from "../../composables/useServices";
import RichText from "../ui/RichText.vue";

const { servicesError, servicesLoading, servicesTree } = useServices();

onMounted(() => {
  loadServices();
});

const cards = computed(() =>
  servicesTree.value.map((service) => {
    const minPrice = findMinTariffPrice(service);
    const hasChildren = Array.isArray(service.children) && service.children.length > 0;

    return {
      ...service,
      hasChildren,
      desc: service.description,
      duration: service.durationLabel,
      image: service.image || "/images/service-moose-cover.jpg",
      priceLabel: Number.isFinite(minPrice) ? `от ${formatPrice(minPrice)}` : "",
      detailsLabel: "Подробнее",
      detailsPath: `/services/${service.path || service.slug || service.id}`,
    };
  })
);

const markImageLoaded = (event) => {
  event.target.classList.add("is-loaded");
};
</script>

<style scoped>
.services {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 32px;
}

.services-state {
  padding: 24px;
  display: grid;
  gap: 8px;
}

.services-state__title {
  margin: 0;
  font-size: 22px;
  color: var(--text-strong);
}

.services-state__text {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.card {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  background: var(--card);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--border);
  box-shadow: 0 18px 40px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transition: transform 280ms ease, box-shadow 280ms ease, border-color 280ms ease;
  display: grid;
  grid-template-rows: 180px 1fr;
  min-height: 360px;
}

.card:hover {
  transform: translateY(-4px);
  border-color: var(--border);
  box-shadow: 0 28px 60px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.media {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.06);
}

.media__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.02);
  transition: transform 350ms ease;
  display: block;
}

.card:hover .media__img {
  transform: scale(1.06);
}

.media-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.1) 55%, rgba(0, 0, 0, 0.18) 100%);
}

.content {
  padding: 16px 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.top {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.title {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
  color: var(--text-strong);
  letter-spacing: 0.2px;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 7px 10px;
  border-radius: 999px;
  font-size: var(--font-size-base);
  color: var(--text);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
}

.price {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-strong);
  padding: 7px 10px;
  border-radius: 999px;
  background: var(--primary-soft);
  border: 1px solid var(--border);
}

.description {
  margin: 0;
  font-size: var(--font-size-base);
  line-height: 1.55;
  color: var(--muted);
  max-height: calc(3 * 1.55em);
  overflow: hidden;
}

.bottom {
  margin-top: auto;
  display: flex;
  align-items: center;
}

.product-grid__more {
  font-size: var(--font-size-base);
}

.arrow {
  margin-left: 8px;
}

@media (max-width: 980px) {
  .services {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .services {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .card {
    grid-template-rows: 160px 1fr;
    min-height: 330px;
    border-radius: 18px;
  }

  .media {
    height: 160px;
  }

  .title {
    font-size: 17px;
  }

  .description {
    font-size: var(--font-size-base);
  }
}
</style>
