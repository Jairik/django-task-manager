from django.apps import AppConfig


class TasksConfig(AppConfig):
    """Registers the tasks app and its default model field type."""

    default_auto_field = "django.db.models.BigAutoField"
    # Must match the Python package name of this app.
    name = "tasks"
