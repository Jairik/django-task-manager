"""View for reopening a done or cancelled task back to todo."""

from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from tasks.models import Task
from tasks.queries import reopen_task_to_todo


@require_POST
def task_revert(request, pk: int, task_pk: int):
    """Reopen a done or cancelled task to todo and return to project detail."""
    # Restrict lookup to tasks that belong to the URL project.
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)
    reopen_task_to_todo(task)
    return redirect("project_detail", pk=pk)
