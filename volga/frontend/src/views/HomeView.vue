<script setup>
import { computed, onMounted, ref } from "vue";
import AppHeader from "../components/AppHeader.vue";
import AppFooter from "../components/AppFooter.vue";
import ProfileHero from "../components/Profile/ProfileHero.vue";
import ProductGrid from "../components/Profile/ProductGrid.vue";
import ScheduleSection from "../components/ScheduleSection.vue";
import FeedbackSection from "../components/FeedbackSection.vue";
import ReviewsSection from "../components/Profile/ReviewsSection.vue";
import ArticleCard from "../components/ArticleCard.vue";
import NewsCard from "../components/NewsCard.vue";
import { getArticles } from "../api/articles";
import { getNewsList } from "../api/news";
import { getNavigationItems } from "../api/navigation";
import { MAIN_MENU_ITEMS } from "../data/navigation";
const menuItems = ref(MAIN_MENU_ITEMS);

const loadingArticles = ref(false);
const articleError = ref("");
const materials = ref([]);

const loadingNews = ref(false);
const newsItems = ref([]);

const latestMaterials = computed(() =>
  [...materials.value]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 4)
);

const latestNews = computed(() =>
  [...newsItems.value]
    .sort((a, b) => new Date(b.published_date).getTime() - new Date(a.published_date).getTime())
    .slice(0, 4)
);

const loadArticles = async () => {
  loadingArticles.value = true;
  articleError.value = "";

  try {
    materials.value = await getArticles();
  } catch (err) {
    console.error("[articles] failed to load", err);
    materials.value = [];
    articleError.value = "Не удалось загрузить материалы.";
  } finally {
    loadingArticles.value = false;
  }
};

const loadNews = async () => {
  loadingNews.value = true;

  try {
    newsItems.value = await getNewsList();
  } catch (err) {
    console.error("[news] failed to load", err);
    newsItems.value = [];
  } finally {
    loadingNews.value = false;
  }
};

const loadNavigation = async () => {
  menuItems.value = await getNavigationItems();
};

onMounted(() => {
  loadNavigation();
  loadArticles();
  loadNews();
});
</script>

<template>
  <div class="profile-page">
    <AppHeader />
    <section class="site-shell">
      <div class="profile-content">
        <ProfileHero :menu-items="menuItems" />

        <section id="services" class="app-section" v-reveal>
          <div class="app-section__inner">
            <h2 class="app-section__title">Услуги и форматы</h2>
            <div class="app-section__content">
              <ProductGrid />
            </div>
          </div>
        </section>

        <section id="feedback" class="app-section" v-reveal>
          <div class="app-section__inner">
            <h2 class="app-section__title">Собери сценарий дня</h2>
            <div class="app-section__content">
              <FeedbackSection />
            </div>
          </div>
        </section>

        <section id="schedule" class="app-section" v-reveal>
          <div class="app-section__inner">
            <h2 class="app-section__title">Расписание занятий</h2>
            <div class="app-section__content">
              <ScheduleSection />
            </div>
          </div>
        </section>

        <section id="reviews" class="app-section" v-reveal>
          <div class="app-section__inner">
            <h2 class="app-section__title">Отзывы</h2>
            <div class="app-section__content">
              <ReviewsSection />
            </div>
          </div>
        </section>

        <section id="articles" class="app-section" v-reveal>
          <div class="app-section__inner">
            <div class="articles-home__head">
              <h2 class="app-section__title articles-home__title">Статьи / Видео</h2>
            </div>

            <div class="articles-home__grid">
              <p v-if="loadingArticles">Загрузка...</p>
              <ArticleCard
                v-for="item in latestMaterials"
                :key="item.slug"
                :item="item"
                :show-description="false"
              />
            </div>
            <p v-if="articleError">{{ articleError }}</p>
            <div class="articles-home__footer">
              <router-link class="articles-home__link btn-secondary" to="/articles">Все материалы / Видео</router-link>
            </div>
          </div>
        </section>

        <section id="news" class="app-section" v-reveal>
          <div class="app-section__inner">
            <div class="news-home__head">
              <h2 class="app-section__title news-home__title">Новости</h2>
            </div>
            <div class="news-home__grid">
              <p v-if="loadingNews">Загрузка...</p>
              <NewsCard v-for="item in latestNews" :key="item.slug" :item="item" />
            </div>
            <div class="news-home__footer">
              <router-link class="news-home__link btn-secondary" to="/news">Все новости</router-link>
            </div>
          </div>
        </section>
      </div>
    </section>
    <AppFooter />
  </div>
</template>

<style scoped>
.profile-page {
  background: var(--bg);
  width: 100%;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  padding: 0 0 60px;
  box-sizing: border-box;
  --header-offset: 124px;
}

.site-shell {
  width: 100%;
  margin: 0 auto;
  position: relative;
  overflow: hidden;
  background: var(--bg);
}

.profile-content {
  padding: 0;
  box-sizing: border-box;
}

.app-section {
  width: 100%;
  padding: var(--section-padding, 64px) 0;
  background: var(--bg);
  scroll-margin-top: var(--header-offset, 120px);
}

.app-section__inner {
  max-width: var(--container-max, 1200px);
  margin: 0 auto;
  padding: 0 28px;
  box-sizing: border-box;
}

.app-section__title {
  margin: 0 0 28px;
  text-align: center;
  font-size: 28px;
  color: var(--text);
}

.app-section__content {
  width: 100%;
}

.articles-home__head {
  display: grid;
  gap: 12px;
  justify-items: center;
}

.articles-home__title {
  margin-bottom: 0;
}

.articles-home__grid {
  margin-top: 22px;
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.articles-home__footer {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

.news-home__head {
  display: grid;
  gap: 12px;
  justify-items: center;
}

.news-home__title {
  margin-bottom: 0;
}

.news-home__grid {
  margin-top: 22px;
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.news-home__footer {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1200px) {
  .articles-home__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .news-home__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .app-section {
    padding: var(--section-padding-mobile, 40px) 0;
  }

  .app-section__inner {
    padding: 0 18px;
  }

  .app-section__title {
    font-size: 24px;
  }

  .articles-home__grid {
    grid-template-columns: 1fr;
  }

  .news-home__grid {
    grid-template-columns: 1fr;
  }

  .articles-home__footer,
  .news-home__footer {
    justify-content: center;
  }

  .articles-home__link,
  .news-home__link {
    width: 100%;
  }
}
</style>
