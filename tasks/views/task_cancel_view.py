"""View for cancelling a task."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.queries import cancel_task


@require_POST
def task_cancel(request, pk: int, task_pk: int):
    """Cancel the task and return to the parent project detail page."""
    # Restrict lookup to tasks that belong to the URL project.
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)
    cancel_task(task)
    return redirect("project_detail", pk=pk)
