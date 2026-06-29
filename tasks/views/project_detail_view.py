"""Project detail page view."""

from django.shortcuts import get_object_or_404, render

from tasks.models import Project
from tasks.queries import build_task_status_sections, get_project_tasks


def project_detail(request, pk: int):
    """Render one project and its tasks grouped by status."""
    project = get_object_or_404(Project, pk=pk)
    tasks = get_project_tasks(project.pk)
    task_sections = build_task_status_sections(tasks)

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "task_sections": task_sections,
        },
    )
