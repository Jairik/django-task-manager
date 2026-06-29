"""Project detail page view."""

from django.shortcuts import get_object_or_404, render

from tasks.limits import normalize_search_query
from tasks.models import Project, TaskStatus
from tasks.queries import (
    build_task_status_sections,
    get_project_tasks,
    partition_overdue_tasks,
)
from tasks.task_list_ui import (
    DUE_FILTER_CHOICES,
    FILTERABLE_PRIORITIES,
    SORT_CHOICES,
    parse_task_list_params,
)


def project_detail(request, pk: int):
    """Render one project and its tasks grouped by status."""
    project = get_object_or_404(Project, pk=pk)
    task_list_ui = parse_task_list_params(request.GET)
    search = normalize_search_query(request.GET.get("q", ""))

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
            "task_list_ui": task_list_ui,
            "task_filter_priorities": FILTERABLE_PRIORITIES,
            "task_due_filter_choices": DUE_FILTER_CHOICES,
            "task_sort_choices": SORT_CHOICES,
        },
    )
