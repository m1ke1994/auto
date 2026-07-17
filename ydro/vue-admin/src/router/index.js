import { createRouter, createWebHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import DashboardView from '../views/DashboardView.vue'
import SiteOverviewView from '../views/SiteOverviewView.vue'
import AnalyticsView from '../views/AnalyticsView.vue'
import AIRecommendationsView from '../views/AIRecommendationsView.vue'
import PlatformLayout from '../layouts/PlatformLayout.vue'
import PlatformOverviewView from '../views/platform/PlatformOverviewView.vue'
import PlatformTableView from '../views/platform/PlatformTableView.vue'
import PlatformAnalyticsView from '../views/platform/PlatformAnalyticsView.vue'
import PlatformSiteDetailView from '../views/platform/PlatformSiteDetailView.vue'
import PlatformClientDetailView from '../views/platform/PlatformClientDetailView.vue'
import PlatformRecommendationDetailView from '../views/platform/PlatformRecommendationDetailView.vue'
import PlatformHealthView from '../views/platform/PlatformHealthView.vue'
import CompetitorAnalysisView from '../views/CompetitorAnalysisView.vue'
import LandingPage from '../views/LandingPage.vue'
import LoginView from '../views/LoginView.vue'
import OnboardingView from '../views/OnboardingView.vue'
import OnboardingPlaceholderView from '../views/OnboardingPlaceholderView.vue'
import RegisterView from '../views/RegisterView.vue'
import SecurityView from '../views/SecurityView.vue'
import BillingView from '../views/BillingView.vue'
import LeadsView from '../views/LeadsView.vue'
import NotificationsView from '../views/NotificationsView.vue'
import NotificationDetailView from '../views/NotificationDetailView.vue'
import AccessRestrictedView from '../views/AccessRestrictedView.vue'
import SectionEditView from '../views/SectionEditView.vue'
import SectionsView from '../views/SectionsView.vue'
import MiniLayoutView from '../views/mini/MiniLayoutView.vue'
import MiniOverviewView from '../views/mini/MiniOverviewView.vue'
import MiniLeadsView from '../views/mini/MiniLeadsView.vue'
import MiniSeoAuditView from '../views/mini/MiniSeoAuditView.vue'
import MiniReportsView from '../views/mini/MiniReportsView.vue'
import MiniSettingsView from '../views/mini/MiniSettingsView.vue'
import MiniIntegrationView from '../views/mini/MiniIntegrationView.vue'
import { applyRouteSeo } from '../config/seo'
import { resolvePostSiteLoadRedirect } from './routePolicy'
import { useAccessStore } from '../stores/access'
import { useAuthStore } from '../stores/auth'
import { useSiteStore } from '../stores/site'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: LandingPage,
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guestOnly: true, title: 'Вход' },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guestOnly: true, title: 'Регистрация' },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: OnboardingView,
    meta: { requiresAuth: true, title: 'Начало работы', onboardingRoute: true },
  },
  {
    path: '/onboarding/create-site',
    name: 'onboarding-create-site',
    component: OnboardingPlaceholderView,
    meta: { requiresAuth: true, title: 'Создание сайта', onboardingRoute: true },
  },
  {
    path: '/onboarding/connect-site',
    name: 'onboarding-connect-site',
    component: OnboardingPlaceholderView,
    meta: { requiresAuth: true, title: 'Подключение сайта', onboardingRoute: true },
  },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true },
    children: [
      { path: 'dashboard', name: 'dashboard', component: DashboardView, meta: { title: 'Панель управления', requiredFeature: 'dashboard_overview' } },
      { path: 'dashboard/notifications', name: 'notifications', component: NotificationsView, meta: { title: 'Уведомления', requiredFeature: 'notifications' } },
      { path: 'dashboard/notifications/:newsId', name: 'notification-detail', component: NotificationDetailView, meta: { title: 'Новость', requiredFeature: 'notifications' } },
      { path: 'access-restricted', name: 'access-restricted', component: AccessRestrictedView, meta: { title: 'Ограничение доступа', billingExempt: true } },
      { path: 'billing', name: 'billing', component: BillingView, meta: { title: 'Оплата', billingExempt: true } },
      { path: 'security', name: 'security', component: SecurityView, meta: { title: 'Безопасность' } },
      { path: 'sites/:siteId/overview', name: 'site-overview', component: SiteOverviewView, props: true, meta: { title: 'Обзор сайта', requiredFeature: 'dashboard_overview' } },
      { path: 'sites/:siteId/sections', name: 'sections', component: SectionsView, props: true, meta: { title: 'Разделы сайта', requiredFeature: 'site_edit' } },
      { path: 'sites/:siteId/analytics', name: 'analytics', component: AnalyticsView, props: true, meta: { title: 'Аналитика', requiredFeature: 'analytics' } },
      { path: 'sites/:siteId/ai-recommendations', name: 'ai-recommendations', component: AIRecommendationsView, props: true, meta: { title: 'AI-рекомендации', requiredFeature: 'ai_recommendations', showLockedFeature: true } },
      {
        path: 'platform',
        component: PlatformLayout,
        meta: { requiresPlatformOwner: true, billingExempt: true },
        children: [
          { path: '', name: 'platform-overview', component: PlatformOverviewView, meta: { title: 'Обзор платформы', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'sites', name: 'platform-sites', component: PlatformTableView, meta: { title: 'Все сайты', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'sites/:siteId', name: 'platform-site-detail', component: PlatformSiteDetailView, meta: { title: 'Сайт платформы', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'analytics', name: 'platform-analytics', component: PlatformAnalyticsView, meta: { title: 'Общая аналитика', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'clients', name: 'platform-clients', component: PlatformTableView, meta: { title: 'Клиенты', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'clients/:clientId', name: 'platform-client-detail', component: PlatformClientDetailView, meta: { title: 'Клиент', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'leads', name: 'platform-leads', component: PlatformTableView, meta: { title: 'Все заявки', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'seo', name: 'platform-seo', component: PlatformTableView, meta: { title: 'SEO платформы', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'recommendations', name: 'platform-recommendations', component: PlatformTableView, meta: { title: 'AI-рекомендации платформы', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'recommendations/:jobId', name: 'platform-recommendation-detail', component: PlatformRecommendationDetailView, meta: { title: 'Технические данные AI', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'subscriptions', name: 'platform-subscriptions', component: PlatformTableView, meta: { title: 'Тарифы и подписки', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'health', name: 'platform-health', component: PlatformHealthView, meta: { title: 'Доступность', requiresPlatformOwner: true, billingExempt: true } },
          { path: 'events', name: 'platform-events', component: PlatformTableView, meta: { title: 'Системные события', requiresPlatformOwner: true, billingExempt: true } },
        ],
      },
      { path: 'sites/:siteId/leads', name: 'leads', component: LeadsView, props: true, meta: { title: 'Лиды', requiredFeature: 'leads' } },
      { path: 'sites/:siteId/seo', name: 'site-seo', component: MiniSeoAuditView, props: true, meta: { title: 'SEO-аудит', requiredFeature: 'seo_audit' } },
      { path: 'sites/:siteId/competitors', name: 'competitor-analysis', component: CompetitorAnalysisView, props: true, meta: { title: 'Анализ конкурентов', requiredFeature: 'competitors' } },
      { path: 'sites/:siteId/integration', name: 'site-integration', component: MiniIntegrationView, props: true, meta: { title: 'Интеграция', requiredFeature: 'telegram' } },
      {
        path: 'mini',
        component: MiniLayoutView,
        children: [
          { path: '', name: 'mini-overview', component: MiniOverviewView, meta: { title: 'Обзор', requiredFeature: 'dashboard_overview' } },
          { path: 'leads', name: 'mini-leads', component: MiniLeadsView, meta: { title: 'Лиды', requiredFeature: 'leads' } },
          { path: 'seo', name: 'mini-seo', component: MiniSeoAuditView, meta: { title: 'SEO-аудит', requiredFeature: 'seo_audit' } },
          { path: 'reports', name: 'mini-reports', component: MiniReportsView, meta: { title: 'Отчёты', requiredFeature: 'reports' } },
          { path: 'settings', name: 'mini-settings', component: MiniSettingsView, meta: { title: 'Настройки', requiredFeature: 'billing_full_access' } },
          { path: 'integration', name: 'mini-integration', component: MiniIntegrationView, meta: { title: 'Интеграция', requiredFeature: 'telegram' } },
        ],
      },
      {
        path: 'sites/:siteId/sections/:sectionId',
        name: 'section-edit',
        component: SectionEditView,
        props: true,
        meta: { title: 'Редактирование раздела', requiredFeature: 'site_edit' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    return { name: 'login' }
  }

  if (to.meta.guestOnly && token) {
    return { name: 'dashboard' }
  }

  if (to.meta.requiresAuth && token) {
    try {
      const authStore = useAuthStore()
      if (!authStore.user) await authStore.getCurrentUser()
      if (to.meta.requiresPlatformOwner && !authStore.user?.permissions?.platform_access) {
        return { name: 'dashboard' }
      }
      const siteStore = useSiteStore()
      if (!siteStore.loaded && !siteStore.loading) {
        try {
          await siteStore.fetchSites()
        } catch {
          // Do not treat a failed sites request as an empty account.
        }
      }
      const postSiteLoadRedirect = resolvePostSiteLoadRedirect(to, siteStore)
      if (postSiteLoadRedirect) return postSiteLoadRedirect
      const accessStore = useAccessStore()
      await accessStore.fetchAccess({ force: true, timeout: 4000 })
      if (to.meta.requiredFeature && !accessStore.can(to.meta.requiredFeature) && !to.meta.showLockedFeature) {
        return {
          name: 'access-restricted',
          query: { feature: to.meta.requiredFeature, from: to.fullPath },
        }
      }
    } catch {
      // Backend feature permissions remain authoritative if the access check is unavailable.
    }
  }

  return true
})

router.afterEach((to) => {
  applyRouteSeo(to)
})

export default router
