import { createRouter, createWebHistory } from 'vue-router'

import { publicSiteUrl } from '../config/api'

const DEFAULT_TITLE = 'Новое Конаково — отдых на природе'
const DEFAULT_DESCRIPTION = 'Новое Конаково — отдых на природе.'

const SERVICE_TITLES = {
  moose: 'Экскурсия в Братство Лосей',
  author: 'Авторские программы',
  master: 'Мастер-классы',
  running: 'Беговые встречи',
}

const humanizeSlug = (value) =>
  decodeURIComponent(String(value || ''))
    .replace(/[-_/]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/(^\w|\s\w)/g, (letter) => letter.toUpperCase())

const getServiceTitle = (route) => {
  const slugPath = String(route.params.slugPath || '').replace(/^\/+|\/+$/g, '')
  if (!slugPath) return 'Услуги'

  const parts = slugPath.split('/').filter(Boolean)
  const key = parts[parts.length - 1]
  return SERVICE_TITLES[key] || humanizeSlug(key)
}

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: 'Новое Конаково — отдых на природе',
      description: 'Природный отдых, экскурсии, мероприятия',
      keywords: 'Новое Конаково, отдых, природа, экскурсии, мероприятия',
    },
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue'),
    meta: {
      title: 'О проекте — Новое Конаково',
      description: 'О проекте, формате отдыха и мероприятиях в Новом Конаково',
      keywords: 'о проекте, Новое Конаково',
    },
  },
  { path: '/moose', redirect: '/brotherhood' },
  {
    path: '/volunteer',
    name: 'volunteer',
    component: () => import('../views/VolunteerView.vue'),
    meta: {
      title: 'Волонтерские программы — Новое Конаково',
      description: 'Волонтерские программы и участие в жизни проекта',
      keywords: 'волонтерские программы, Новое Конаково',
    },
  },
  {
    path: '/running-club',
    name: 'running-club',
    component: () => import('../views/RunningClubView.vue'),
    meta: {
      title: 'Беговой клуб — Новое Конаково',
      description: 'Беговые встречи и тренировки в природной среде',
      keywords: 'беговой клуб, Новое Конаково',
    },
  },
  { path: '/bronze-club', redirect: '/running-club' },
  {
    path: '/schedule',
    name: 'schedule',
    component: () => import('../views/ScheduleView.vue'),
    meta: {
      title: 'Расписание — Новое Конаково',
      description: 'Актуальное расписание мероприятий и активностей',
      keywords: 'расписание, мероприятия, Новое Конаково',
    },
  },
  {
    path: '/articles',
    name: 'articles',
    component: () => import('../views/ArticlesView.vue'),
    meta: {
      title: 'Статьи — Новое Конаково',
      description: 'Статьи и материалы о проекте, отдыхе и экскурсиях',
      keywords: 'статьи, Новое Конаково',
    },
  },
  {
    path: '/video',
    name: 'video',
    component: () => import('../views/ArticlesView.vue'),
    meta: {
      title: 'Видео — Новое Конаково',
      description: 'Видео о природном отдыхе, экскурсиях и мероприятиях',
      keywords: 'видео, Новое Конаково',
    },
  },
  {
    path: '/articles/:slug',
    name: 'article-single',
    component: () => import('../views/ArticlesSingleView.vue'),
    meta: {
      title: 'Статья — Новое Конаково',
      description: 'Материал в разделе статей и видео',
      keywords: 'статья, Новое Конаково',
    },
  },
  {
    path: '/news',
    name: 'news',
    component: () => import('../views/NewsView.vue'),
    meta: {
      title: 'Новости — Новое Конаково',
      description: 'Новости и анонсы проекта Новое Конаково',
      keywords: 'новости, Новое Конаково',
    },
  },
  {
    path: '/news/:slug',
    name: 'news-single',
    component: () => import('../views/NewsSingleView.vue'),
    meta: {
      title: 'Новость — Новое Конаково',
      description: 'Детальная страница новости проекта',
      keywords: 'новость, Новое Конаково',
    },
  },
  {
    path: '/services',
    name: 'services',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: 'Услуги — Новое Конаково',
      description: 'Форматы отдыха и экскурсии в Новом Конаково',
      keywords: 'услуги, экскурсии, Новое Конаково',
    },
  },
  {
    path: '/services/:slugPath(.*)',
    name: 'service-detail',
    component: () => import('../views/ServiceDetailView.vue'),
    meta: {
      title: (route) => `${getServiceTitle(route)} — Новое Конаково`,
      description: 'Форматы отдыха и экскурсии в Новом Конаково',
      keywords: 'услуги, экскурсии, Новое Конаково',
    },
  },
  {
    path: '/contacts',
    name: 'contacts',
    component: () => import('../views/ContactsView.vue'),
    meta: {
      title: 'Контакты — Новое Конаково',
      description: 'Контакты и способы связи с проектом Новое Конаково',
      keywords: 'контакты, Новое Конаково',
    },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: () => import('../views/PrivacyView.vue'),
    meta: {
      title: 'Политика конфиденциальности — Новое Конаково',
      description: 'Политика конфиденциальности проекта',
      keywords: 'политика конфиденциальности, Новое Конаково',
    },
  },
  {
    path: '/terms',
    name: 'terms',
    component: () => import('../views/TermsView.vue'),
    meta: {
      title: 'Условия использования — Новое Конаково',
      description: 'Условия использования сайта',
      keywords: 'условия использования, Новое Конаково',
    },
  },
  {
    path: '/brotherhood',
    name: 'brotherhood',
    component: () => import('../views/BrotherhoodView.vue'),
    meta: {
      title: 'Братство Лосей — Новое Конаково',
      description: 'Экскурсионное направление Братство Лосей',
      keywords: 'Братство Лосей, Новое Конаково',
    },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) {
      return {
        el: to.hash,
        top: 96,
        behavior: 'smooth',
      }
    }
    return { left: 0, top: 0 }
  },
  routes,
})

router.afterEach((to) => {
  const routeTitle = typeof to.meta.title === 'function' ? to.meta.title(to) : to.meta.title
  const routeDescription =
    typeof to.meta.description === 'function' ? to.meta.description(to) : to.meta.description
  const routeKeywords = typeof to.meta.keywords === 'function' ? to.meta.keywords(to) : to.meta.keywords

  document.title = routeTitle || DEFAULT_TITLE

  const descriptionTag = document.querySelector('meta[name="description"]')
  if (descriptionTag) {
    descriptionTag.setAttribute('content', routeDescription || DEFAULT_DESCRIPTION)
  }

  const keywordsTag = document.querySelector('meta[name="keywords"]')
  if (keywordsTag) {
    keywordsTag.setAttribute('content', routeKeywords || 'Новое Конаково, отдых, природа')
  }

  const canonical = document.querySelector('link[rel="canonical"]')
  if (canonical && publicSiteUrl) {
    canonical.setAttribute('href', `${publicSiteUrl}${to.fullPath}`)
  }
})

export default router
