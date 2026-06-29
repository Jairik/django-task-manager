"""Project detail page view."""

from django.shortcuts import get_object_or_404, render

from tasks.models import Project, TaskStatus
from tasks.queries import (
    build_task_status_sections,
    get_project_tasks,
    partition_overdue_tasks,
)


def project_detail(request, pk: int):
    """Render one project and its tasks grouped by status."""
    project = get_object_or_404(Project, pk=pk)
    search = request.GET.get("q", "").strip()

    # Materialize once so we can group tasks and tally header stats with one query.
    tasks = list(get_project_tasks(project.pk, search=search))
    overdue_tasks, remaining_tasks = partition_overdue_tasks(tasks)
    task_sections = build_task_status_sections(remaining_tasks)

    # Summary stats for the header card, counted across every task.
    task_count = len(tasks)
    done_count = sum(1 for task in tasks if task.status == TaskStatus.DONE)
    progress = round(done_count / task_count * 100) if task_count else 0

    return render(
        request,
        "projects/project_detail.html",
        {
            "project": project,
            "overdue_tasks": overdue_tasks,
            "task_sections": task_sections,
            "task_count": task_count,
            "done_count": done_count,
            "progress": progress,
        },
    )
