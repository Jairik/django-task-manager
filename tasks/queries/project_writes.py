"""Write-side query helpers for projects."""

from tasks.models import Project


def update_project(project: Project) -> Project:
    """Persist project field changes from the edit form."""
    project.save()
    return project


def delete_project(project: Project) -> None:
    """Delete a project and its tasks (CASCADE on the Task FK)."""
    project.delete()
