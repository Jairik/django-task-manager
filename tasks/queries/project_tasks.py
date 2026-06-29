"""Task queryset helpers for the project detail page.

Loads all tasks for one project and groups them by status for kanban-style
sections. Uses a single SQL query plus in-memory grouping (see
docs/scalingConcerns.md).
"""

from collections.abc import Iterable
from typing import Any

from django.db.models import F, QuerySet

from tasks.models import Task, TaskStatus

# Fixed section order for the project detail template (todo → cancelled).
TASK_STATUS_SECTION_ORDER: tuple[TaskStatus, ...] = (
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.DONE,
    TaskStatus.CANCELLED,
)


def get_project_tasks(project_id: int) -> QuerySet[Task]:
    """Return all tasks for a project, ordered for within-section display.

    Uses task_project_id_idx. Tasks are sorted by due date (nulls last), then
    name, then primary key as a stable tiebreaker.
    """
    return (
        Task.objects.filter(project_id=project_id)
        .order_by(F("due_date").asc(nulls_last=True), "name", "pk")
    )


def build_task_status_sections(tasks: Iterable[Task]) -> list[dict[str, Any]]:
    """Group tasks into fixed status sections for the project detail page.

    Always returns all four sections (even when empty) so the template layout
    stays predictable. Preserves the iteration order of ``tasks`` within each
    section.
    """
    # Bucket tasks by status value before applying display order.
    tasks_by_status: dict[str, list[Task]] = {status.value: [] for status in TASK_STATUS_SECTION_ORDER}

    for task in tasks:
        tasks_by_status[task.status].append(task)

    sections: list[dict[str, Any]] = []
    for status in TASK_STATUS_SECTION_ORDER:
        sections.append(
            {
                "status": status,
                "label": status.label,
                "tasks": tasks_by_status[status.value],
            }
        )

    return sections
