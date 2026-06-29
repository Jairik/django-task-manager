"""URL routes for the tasks app."""

from django.urls import path

from . import views

urlpatterns = [
    # Landing page served at the site root.
    path("", views.home, name="home"),
]
