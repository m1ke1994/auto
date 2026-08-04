from django.urls import path
from platform_admin.views import AuditLogView, AnalyticsView, ClientDetailView, ClientsView, HealthView, LeadsView, OverviewView, RecommendationDetailView, RecommendationsView, SEOAuditsView, SiteDetailView, SitesView, SubscriptionsView, TemplateDetailView

urlpatterns = [
    path("overview/", OverviewView.as_view()), path("sites/", SitesView.as_view()), path("sites/<int:site_id>/", SiteDetailView.as_view()), path("sites/<int:site_id>/analytics/", AnalyticsView.as_view()), path("templates/<int:template_id>/", TemplateDetailView.as_view()), path("analytics/", AnalyticsView.as_view()), path("clients/", ClientsView.as_view()), path("clients/<int:client_id>/", ClientDetailView.as_view()), path("leads/", LeadsView.as_view()), path("recommendations/", RecommendationsView.as_view()), path("recommendations/<uuid:job_id>/", RecommendationDetailView.as_view()), path("seo/", SEOAuditsView.as_view()), path("subscriptions/", SubscriptionsView.as_view()), path("health/", HealthView.as_view()), path("audit/", AuditLogView.as_view()),
]
