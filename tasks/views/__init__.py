"""HTTP views for the tasks app."""

from .home_view import home
from .project_create_view import project_create
from .project_detail_view import project_detail
from .task_create_view import task_create

__all__ = ["home", "project_create", "project_detail", "task_create"]
