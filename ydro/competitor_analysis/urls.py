from django.urls import path

from competitor_analysis.views import (
    CompetitorAnalysisCreateView,
    CompetitorAnalysisDetailView,
    CompetitorAnalysisListView,
    CompetitorAnalysisPdfView,
)

urlpatterns = [
    path("<int:site_id>/competitors/", CompetitorAnalysisListView.as_view(), name="competitor-analysis-list"),
    path("<int:site_id>/competitors/analyze/", CompetitorAnalysisCreateView.as_view(), name="competitor-analysis-create"),
    path(
        "<int:site_id>/competitors/<int:analysis_id>/pdf/",
        CompetitorAnalysisPdfView.as_view(),
        name="competitor-analysis-pdf",
    ),
    path(
        "<int:site_id>/competitors/<int:analysis_id>/",
        CompetitorAnalysisDetailView.as_view(),
        name="competitor-analysis-detail",
    ),
]
