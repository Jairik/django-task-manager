"""View for creating a task within a project."""

from django.shortcuts import get_object_or_404, redirect, render

from tasks.forms import TaskForm
from tasks.models import Project
from tasks.queries import create_task_for_project


def task_create(request, pk: int):
    """Show the new-task form (GET) or save a task under a project (POST)."""
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            # Attach the parent project before persisting (see TaskForm.save).
            task = form.save(commit=False)
            task.project = project
            create_task_for_project(task)
            return redirect("project_detail", pk=project.pk)
    else:
        form = TaskForm()

    return render(
        request,
        "tasks/task_create_form.html",
        {
            "project": project,
            "form": form,
            "submit_label": "Create task",
        },
    )
