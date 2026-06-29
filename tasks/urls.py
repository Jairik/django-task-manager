"""URL routes for the tasks app."""

from django.urls import path

from tasks.views import home, project_create, project_detail

urlpatterns = [
    path("", home, name="home"),
    path("projects/new/", project_create, name="project_create"),
    path("projects/<int:pk>/", project_detail, name="project_detail"),
]
