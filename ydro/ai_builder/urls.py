from django.urls import path
from . import views
urlpatterns = [
    path('projects/<uuid:pk>/versions/', views.ProjectVersions.as_view()),
    path('projects/<uuid:pk>/versions/<uuid:version_id>/restore/', views.VersionRestore.as_view()),
    path('projects/<uuid:pk>/versions/<uuid:version_id>/export/', views.VersionExport.as_view()),
    path('projects/<uuid:pk>/blocks/', views.Blocks.as_view()),
    path('projects/<uuid:pk>/blocks/<str:block>/regenerate/', views.RegenerateBlock.as_view()),
    path('projects/<uuid:pk>/block-edits/<uuid:edit_id>/<str:action>/', views.BlockDecision.as_view()),
    path("config/", views.Config.as_view()),
    path("projects/", views.Projects.as_view()),
    path("projects/<uuid:pk>/", views.Detail.as_view()),
    path("projects/<uuid:pk>/edit/", views.Edit.as_view()),
    path("projects/<uuid:pk>/publish/<int:revision>/", views.Publish.as_view()),
    path("projects/<uuid:pk>/export/<int:revision>/", views.Export.as_view()),
    path("projects/<uuid:pk>/cinematic-export/", views.CinematicExport.as_view()),
]
