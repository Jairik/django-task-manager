"""View for editing an existing task."""

from django.shortcuts import get_object_or_404, redirect, render

from tasks.forms import TaskForm
from tasks.models import Project, Task
from tasks.queries import update_task_for_project


def task_edit(request, pk: int, task_pk: int):
    """Show the edit-task form (GET) or save changes (POST)."""
    project = get_object_or_404(Project, pk=pk)
    task = get_object_or_404(Task, pk=task_pk, project_id=pk)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)

        if form.is_valid():
            update_task_for_project(form.save())
            return redirect("project_detail", pk=project.pk)
    else:
        form = TaskForm(instance=task)

    return render(
        request,
        "tasks/task_edit_form.html",
        {
            "project": project,
            "task": task,
            "form": form,
            "submit_label": "Save changes",
        },
    )
