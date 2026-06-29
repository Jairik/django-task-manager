"""View for reverting a completed task back to todo."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.queries import revert_task_to_todo


@require_POST
def task_revert(request, pk: int, task_pk: int):
    """Revert a done task to todo and return to the parent project detail page."""
    # Restrict lookup to tasks that belong to the URL project.
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)
    revert_task_to_todo(task)
    return redirect("project_detail", pk=pk)
