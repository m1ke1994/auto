import { createRouter, createWebHistory } from 'vue-router'

const DEFAULT_TITLE = 'АРТ СТРОЙ | Остекление и архитектурные решения'
const DEFAULT_DESCRIPTION =
  'Остекление, душевые стекла, зеркальные панно, перегородки и ограждения. Инженерно точные решения в премиальной архитектурной эстетике.'
const DEFAULT_KEYWORDS =
  'остекление, металлоконструкции, фасадное остекление, стеклянные перегородки, душевые стекла, зеркальные панно, перегородки и ограждения, современные фасады, архитектурное остекление, строительная компания'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: 'АРТ СТРОЙ | Главная',
      description:
        'Современные фасады, душевые стекла, зеркальные панно и перегородки. Комплексный инженерный подход и премиальная эстетика.',
      keywords: DEFAULT_KEYWORDS,
    },
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('../views/AboutView.vue'),
    meta: {
      title: 'О компании | АРТ СТРОЙ',
      description:
        'АРТ СТРОЙ: инженерная точность, надежные материалы и современный подход к реализации проектов остекления.',
      keywords: DEFAULT_KEYWORDS,
    },
  },
  {
    path: '/projects',
    name: 'projects',
    component: () => import('../views/project-detail.vue'),
    meta: {
      title: 'Наши проекты | АРТ СТРОЙ',
      description:
        'Портфолио проектов: душевые стекла, зеркальные панно, перегородки и ограждения. Реализованные решения с акцентом на качество.',
      keywords:
        'душевые стекла, зеркальные панно, перегородки и ограждения, остекление, проекты',
    },
  },
  {
    path: '/project-detail',
    redirect: '/projects',
  },
  {
    path: '/privacy-policy',
    name: 'privacy-policy',
    component: () => import('../views/PrivacyPolicyView.vue'),
    meta: {
      title: 'Политика конфиденциальности | АРТ СТРОЙ',
      description:
        'Политика конфиденциальности и порядок обработки персональных данных пользователей сайта АРТ СТРОЙ.',
      keywords:
        'политика конфиденциальности, персональные данные, обработка данных, АРТ СТРОЙ',
    },
  },
  {
    path: '/data-consent',
    name: 'data-consent',
    component: () => import('../views/DataConsentView.vue'),
    meta: {
      title: 'Согласие на обработку данных | АРТ СТРОЙ',
      description:
        'Согласие на обработку персональных данных для обратной связи и подготовки коммерческих предложений.',
      keywords:
        'согласие на обработку данных, персональные данные, АРТ СТРОЙ',
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }

    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
      }
    }

    return { top: 0, behavior: 'smooth' }
  },
})

const setMeta = (name, content, property = false) => {
  const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`
  let element = document.head.querySelector(selector)

  if (!element) {
    element = document.createElement('meta')
    if (property) {
      element.setAttribute('property', name)
    } else {
      element.setAttribute('name', name)
    }
    document.head.appendChild(element)
  }

  element.setAttribute('content', content)
}

const setCanonical = (href) => {
  let canonical = document.head.querySelector('link[rel="canonical"]')
  if (!canonical) {
    canonical = document.createElement('link')
    canonical.setAttribute('rel', 'canonical')
    document.head.appendChild(canonical)
  }
  canonical.setAttribute('href', href)
}

router.afterEach((to) => {
  const title = to.meta.title || DEFAULT_TITLE
  const description = to.meta.description || DEFAULT_DESCRIPTION
  const keywords = to.meta.keywords || DEFAULT_KEYWORDS

  document.title = title
  setMeta('description', description)
  setMeta('keywords', keywords)
  setMeta('og:title', title, true)
  setMeta('og:description', description, true)
  setMeta('og:url', window.location.href, true)
  setMeta('twitter:title', title)
  setMeta('twitter:description', description)
  setCanonical(window.location.href)
})

export default router
