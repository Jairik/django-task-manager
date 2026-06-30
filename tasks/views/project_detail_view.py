"""Project detail page view."""

from django.shortcuts import get_object_or_404, render

from tasks.models import Project, Task, TaskStatus
from tasks.queries import (
    build_task_status_sections,
    get_project_tasks,
    partition_overdue_tasks,
    task_list_filters_from_ui_state,
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
    filters = task_list_filters_from_ui_state(task_list_ui)

    # Materialize once so we can group tasks and tally header stats with one query.
    tasks = list(get_project_tasks(project.pk, search=task_list_ui.search, filters=filters))
    overdue_tasks, remaining_tasks = partition_overdue_tasks(tasks)
    task_sections = build_task_status_sections(remaining_tasks)

    # Header stats reflect the filtered task list; relabel when search/filters are active.
    task_count = len(tasks)
    done_count = sum(1 for task in tasks if task.status == TaskStatus.DONE)
    progress = round(done_count / task_count * 100) if task_count else 0
    stats_are_filtered = bool(task_list_ui.search) or task_list_ui.active_filter_count > 0
    total_task_count = (
        Task.objects.filter(project=project).count() if stats_are_filtered else None
    )

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
            "stats_are_filtered": stats_are_filtered,
            "total_task_count": total_task_count,
            "task_list_ui": task_list_ui,
            "task_filter_priorities": FILTERABLE_PRIORITIES,
            "task_due_filter_choices": DUE_FILTER_CHOICES,
            "task_sort_choices": SORT_CHOICES,
        },
    )
