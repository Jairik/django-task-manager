"""URL routes for the tasks app."""

from django.urls import path

from tasks.views import home, project_create

urlpatterns = [
    path("", home, name="home"),
    path("projects/new/", project_create, name="project_create"),
]
