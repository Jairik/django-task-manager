"""View for advancing a task one step along todo → in_progress → done."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.queries import advance_task_status


@require_POST
def task_advance(request, pk: int, task_pk: int):
    """Advance the task status and return to the parent project detail page."""
    # Restrict lookup to tasks that belong to the URL project.
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)
    advance_task_status(task)
    return redirect("project_detail", pk=pk)
