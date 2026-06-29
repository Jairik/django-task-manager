"""HTTP views for the tasks app."""

from .home_view import home
from .project_create_view import project_create
from .project_delete_view import project_delete
from .project_detail_view import project_detail
from .project_edit_view import project_edit
from .task_advance_view import task_advance
from .task_revert_view import task_revert
from .task_create_view import task_create
from .task_delete_view import task_delete
from .task_edit_view import task_edit

__all__ = [
    "home",
    "project_create",
    "project_delete",
    "project_detail",
    "project_edit",
    "task_advance",
    "task_revert",
    "task_create",
    "task_delete",
    "task_edit",
]
