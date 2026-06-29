"""URL routes for the tasks app."""

from django.urls import path

from tasks.views import (
    home,
    project_create,
    project_detail,
    task_advance,
    task_cancel,
    task_create,
    task_delete,
    task_edit,
)

urlpatterns = [
    path("", home, name="home"),
    path("projects/new/", project_create, name="project_create"),
    path("projects/<int:pk>/", project_detail, name="project_detail"),
    path("projects/<int:pk>/tasks/new/", task_create, name="task_create"),
    path("projects/<int:pk>/tasks/<int:task_pk>/advance/", task_advance, name="task_advance"),
    path("projects/<int:pk>/tasks/<int:task_pk>/cancel/", task_cancel, name="task_cancel"),
    path("projects/<int:pk>/tasks/<int:task_pk>/edit/", task_edit, name="task_edit"),
    path("projects/<int:pk>/tasks/<int:task_pk>/delete/", task_delete, name="task_delete"),
]
