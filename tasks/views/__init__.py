"""HTTP views for the tasks app."""

from .home_view import home
from .project_create_view import project_create

__all__ = ["home", "project_create"]
