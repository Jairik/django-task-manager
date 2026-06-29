"""Root URL configuration for the entire project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Built-in Django admin interface.
    path("admin/", admin.site.urls),
    # Public-facing pages handled by the tasks app.
    path("", include("tasks.urls")),
]
