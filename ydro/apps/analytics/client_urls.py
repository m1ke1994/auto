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
    path("<int:site_id>/analytics/overview/", AdminSiteAnalyticsSummaryView.as_view(), name="client-site-analytics-overview"),
    path("<int:site_id>/analytics/heatmap/", AdminSiteAnalyticsHeatmapView.as_view(), name="client-site-analytics-heatmap"),
    path("<int:site_id>/analytics/scrollmap/", AdminSiteAnalyticsScrollmapView.as_view(), name="client-site-analytics-scrollmap"),
    path("<int:site_id>/analytics/sessions/", AdminSiteAnalyticsSessionsView.as_view(), name="client-site-analytics-sessions"),
    path("<int:site_id>/analytics/sessions/<str:session_id>/", AdminSiteAnalyticsSessionDetailView.as_view(), name="client-site-analytics-session-detail"),
    path("<int:site_id>/analytics/paths/", AdminSiteAnalyticsPathsView.as_view(), name="client-site-analytics-paths"),
    path("<int:site_id>/analytics/funnels/", AdminSiteAnalyticsFunnelsView.as_view(), name="client-site-analytics-funnels"),
    path("<int:site_id>/analytics/events/", AdminSiteAnalyticsEventsView.as_view(), name="client-site-analytics-events"),
    path("<int:site_id>/analytics/pages/", AdminSiteAnalyticsPagesView.as_view(), name="client-site-analytics-pages"),
    path("<int:site_id>/analytics/errors/", AdminSiteAnalyticsErrorsView.as_view(), name="client-site-analytics-errors"),
    path("<int:site_id>/analytics/performance/", AdminSiteAnalyticsPerformanceView.as_view(), name="client-site-analytics-performance"),
    path("<int:site_id>/analytics/recommendations/", AdminSiteAnalyticsRecommendationsView.as_view(), name="client-site-analytics-recommendations"),
]
