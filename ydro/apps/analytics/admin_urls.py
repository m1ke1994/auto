from django.urls import path

from .views import (
    AdminSiteAnalyticsErrorsView,
    AdminSiteAnalyticsEventsView,
    AdminSiteAnalyticsFunnelsView,
    AdminSiteAnalyticsHeatmapView,
    AdminSiteAnalyticsPagesView,
    AdminSiteAnalyticsPathsView,
    AdminSiteAnalyticsPerformanceView,
    AdminSiteAnalyticsRecommendationsView,
    AdminSiteAnalyticsScrollmapView,
    AdminSiteAnalyticsSessionDetailView,
    AdminSiteAnalyticsSessionsView,
    AdminSiteAnalyticsSummaryView,
)

urlpatterns = [
    path("my-sites/<int:site_id>/analytics/summary/", AdminSiteAnalyticsSummaryView.as_view(), name="admin-site-analytics-summary"),
    path("my-sites/<int:site_id>/analytics/overview/", AdminSiteAnalyticsSummaryView.as_view(), name="admin-site-analytics-overview"),
    path("my-sites/<int:site_id>/analytics/heatmap/", AdminSiteAnalyticsHeatmapView.as_view(), name="admin-site-analytics-heatmap"),
    path("my-sites/<int:site_id>/analytics/scrollmap/", AdminSiteAnalyticsScrollmapView.as_view(), name="admin-site-analytics-scrollmap"),
    path("my-sites/<int:site_id>/analytics/sessions/", AdminSiteAnalyticsSessionsView.as_view(), name="admin-site-analytics-sessions"),
    path("my-sites/<int:site_id>/analytics/sessions/<str:session_id>/", AdminSiteAnalyticsSessionDetailView.as_view(), name="admin-site-analytics-session-detail"),
    path("my-sites/<int:site_id>/analytics/paths/", AdminSiteAnalyticsPathsView.as_view(), name="admin-site-analytics-paths"),
    path("my-sites/<int:site_id>/analytics/funnels/", AdminSiteAnalyticsFunnelsView.as_view(), name="admin-site-analytics-funnels"),
    path("my-sites/<int:site_id>/analytics/events/", AdminSiteAnalyticsEventsView.as_view(), name="admin-site-analytics-events"),
    path("my-sites/<int:site_id>/analytics/pages/", AdminSiteAnalyticsPagesView.as_view(), name="admin-site-analytics-pages"),
    path("my-sites/<int:site_id>/analytics/errors/", AdminSiteAnalyticsErrorsView.as_view(), name="admin-site-analytics-errors"),
    path("my-sites/<int:site_id>/analytics/performance/", AdminSiteAnalyticsPerformanceView.as_view(), name="admin-site-analytics-performance"),
    path("my-sites/<int:site_id>/analytics/recommendations/", AdminSiteAnalyticsRecommendationsView.as_view(), name="admin-site-analytics-recommendations"),
]
