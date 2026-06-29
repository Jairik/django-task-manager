"""View for deleting a task."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.queries import delete_task_for_project


@require_POST
def task_delete(request, pk: int, task_pk: int):
    """Delete the task and return to the parent project detail page."""
    # Restrict lookup to tasks that belong to the URL project.
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)
    delete_task_for_project(task)
    return redirect("project_detail", pk=pk)
