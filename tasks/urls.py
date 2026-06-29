"""URL routes for the tasks app."""

from django.urls import path

from tasks.views import (
    home,
    project_create,
    project_delete,
    project_detail,
    project_edit,
    task_advance,
    task_revert,
    task_create,
    task_delete,
    task_edit,
)

urlpatterns = [
    path("", home, name="home"),
    path("projects/new/", project_create, name="project_create"),
    path("projects/<int:pk>/", project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", project_edit, name="project_edit"),
    path("projects/<int:pk>/delete/", project_delete, name="project_delete"),
    path("projects/<int:pk>/tasks/new/", task_create, name="task_create"),
    path("projects/<int:pk>/tasks/<int:task_pk>/advance/", task_advance, name="task_advance"),
    path("projects/<int:pk>/tasks/<int:task_pk>/revert/", task_revert, name="task_revert"),
    path("projects/<int:pk>/tasks/<int:task_pk>/edit/", task_edit, name="task_edit"),
    path("projects/<int:pk>/tasks/<int:task_pk>/delete/", task_delete, name="task_delete"),
]
