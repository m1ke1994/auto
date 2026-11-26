from django.urls import path
from . import views
urlpatterns = [
    path("config/", views.Config.as_view()),
    path("projects/", views.Projects.as_view()),
    path("projects/<uuid:pk>/", views.Detail.as_view()),
    path("projects/<uuid:pk>/edit/", views.Edit.as_view()),
    path("projects/<uuid:pk>/publish/<int:revision>/", views.Publish.as_view()),
    path("projects/<uuid:pk>/export/<int:revision>/", views.Export.as_view()),
    path("projects/<uuid:pk>/cinematic-export/", views.CinematicExport.as_view()),
]
