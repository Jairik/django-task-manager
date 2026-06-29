"""View for deleting a project."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Project
from tasks.queries import delete_project


@require_POST
def project_delete(request, pk: int):
    """Delete the project and return to the home page."""
    project = get_object_or_404(Project, pk=pk)
    delete_project(project)
    return redirect("home")
