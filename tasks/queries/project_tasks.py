"""Task queryset helpers for the project detail page.

Loads all tasks for one project and groups them by status for kanban-style
sections. Uses a single SQL query plus in-memory grouping (see
docs/scalingConcerns.md).
"""

from collections.abc import Iterable
from datetime import date
from typing import Any

from django.db.models import F, Min, QuerySet
from django.utils import timezone

from tasks.models import Project, Task, TaskStatus

# Fixed section order for the project detail template (todo → cancelled).
TASK_STATUS_SECTION_ORDER: tuple[TaskStatus, ...] = (
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.DONE,
    TaskStatus.CANCELLED,
)

# Open statuses eligible for the overdue bucket on the project detail page.
_OPEN_STATUSES: frozenset[TaskStatus] = frozenset(
    {TaskStatus.TODO, TaskStatus.IN_PROGRESS}
)


def refresh_project_soonest_due_date(project: Project) -> None:
    """Recompute ``Project.soonest_due_date`` from dated tasks under the project.

    Uses the earliest non-null task ``due_date`` (see docs/schema.md). Sets the
    field to ``None`` when the project has no dated tasks.
    """
    soonest_due_date = (
        Task.objects.filter(project_id=project.pk, due_date__isnull=False)
        .aggregate(soonest=Min("due_date"))
        .get("soonest")
    )

    project.soonest_due_date = soonest_due_date
    project.save(update_fields=["soonest_due_date", "updated_at"])


def create_task_for_project(task: Task) -> Task:
    """Persist a new task and refresh the parent project's ``soonest_due_date``.

    The caller must set ``task.project`` and build field values (e.g. from
    ``TaskForm``) before calling. Returns the saved task instance.
    """
    task.save()
    refresh_project_soonest_due_date(task.project)
    return task


def get_project_tasks(project_id: int) -> QuerySet[Task]:
    """Return all tasks for a project, ordered for within-section display.

    Uses task_project_id_idx. Tasks are sorted by due date (nulls last), then
    name, then primary key as a stable tiebreaker.
    """
    return (
        Task.objects.filter(project_id=project_id)
        .order_by(F("due_date").asc(nulls_last=True), "name", "pk")
    )


def partition_overdue_tasks(
    tasks: Iterable[Task],
    today: date | None = None,
) -> tuple[list[Task], list[Task]]:
    """Split open tasks with a past due date into a separate overdue list.

    A task is overdue when it is todo or in progress, has a due date, and that
    date is strictly before ``today``. Overdue tasks are excluded from the list
    returned for status-section grouping.
    """
    if today is None:
        today = timezone.localdate()

    overdue_tasks: list[Task] = []
    remaining_tasks: list[Task] = []

    for task in tasks:
        if (
            task.status in _OPEN_STATUSES
            and task.due_date is not None
            and task.due_date < today
        ):
            overdue_tasks.append(task)
        else:
            remaining_tasks.append(task)

    return overdue_tasks, remaining_tasks


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
