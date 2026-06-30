"""Apply project-detail task list filters and sort to a Task queryset.

Toolbar URL params are parsed in ``tasks.task_list_ui``; this module maps that
state onto database filters and ``order_by`` clauses.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from django.db.models import F, QuerySet
from django.utils import timezone

from tasks.models import Task, TaskStatus
from tasks.queries.list_filter_common import (
    apply_priority_sort,
    effective_due_filter,
    week_bounds,
)
from tasks.task_list_ui import DEFAULT_DUE_FILTER, DEFAULT_SORT_DIR, DEFAULT_SORT_FIELD

if TYPE_CHECKING:
    from tasks.task_list_ui import TaskListUIState

# Open statuses used by the overdue due-date bucket filter.
_OPEN_STATUSES: frozenset[TaskStatus] = frozenset(
    {TaskStatus.TODO, TaskStatus.IN_PROGRESS}
)

# Sort fields supported by the toolbar (excludes removed manual order).
_VALID_SORT_FIELDS = frozenset({"due_date", "priority", "created", "updated", "name"})
_VALID_SORT_DIRS = frozenset({"asc", "desc"})


@dataclass(frozen=True)
class TaskListFilters:
    """Filter and sort options for the project detail task list."""

    selected_priorities: tuple[str, ...] = ()
    due_filter: str = DEFAULT_DUE_FILTER
    due_on: date | None = None
    sort_by: str = DEFAULT_SORT_FIELD
    sort_dir: str = DEFAULT_SORT_DIR


def task_list_filters_from_ui_state(ui_state: "TaskListUIState") -> TaskListFilters:
    """Build query-layer filters from parsed toolbar UI state."""
    return TaskListFilters(
        selected_priorities=ui_state.selected_priorities,
        due_filter=ui_state.due_filter,
        due_on=ui_state.due_on,
        sort_by=ui_state.sort_by,
        sort_dir=ui_state.sort_dir,
    )


def apply_task_list_filters(
    queryset: QuerySet[Task],
    filters: TaskListFilters,
    *,
    today: date | None = None,
) -> QuerySet[Task]:
    """Narrow a task queryset by toolbar priority and due-date filters."""
    if today is None:
        today = timezone.localdate()

    if filters.selected_priorities:
        queryset = queryset.filter(priority__in=filters.selected_priorities)

    due_filter = effective_due_filter(
        filters.due_filter,
        filters.due_on,
        default_due_filter=DEFAULT_DUE_FILTER,
    )

    if due_filter == "overdue":
        queryset = queryset.filter(
            status__in=[status.value for status in _OPEN_STATUSES],
            due_date__lt=today,
        )
    elif due_filter == "today":
        queryset = queryset.filter(due_date=today)
    elif due_filter == "this_week":
        week_start, week_end = week_bounds(today)
        queryset = queryset.filter(due_date__gte=week_start, due_date__lte=week_end)
    elif due_filter == "no_date":
        queryset = queryset.filter(due_date__isnull=True)
    elif due_filter == "by_date" and filters.due_on is not None:
        queryset = queryset.filter(
            due_date__isnull=False,
            due_date__lte=filters.due_on,
        )

    return queryset


def apply_task_list_sort(queryset: QuerySet[Task], filters: TaskListFilters) -> QuerySet[Task]:
    """Order a task queryset by the toolbar sort field and direction."""
    sort_by = filters.sort_by if filters.sort_by in _VALID_SORT_FIELDS else DEFAULT_SORT_FIELD
    sort_dir = filters.sort_dir if filters.sort_dir in _VALID_SORT_DIRS else DEFAULT_SORT_DIR
    descending = sort_dir == "desc"

    if sort_by == "due_date":
        due_order = F("due_date").desc(nulls_last=True) if descending else F("due_date").asc(nulls_last=True)
        return queryset.order_by(due_order, "pk")

    if sort_by == "priority":
        return apply_priority_sort(queryset, descending=descending)

    if sort_by == "created":
        created_field = "-created_at" if descending else "created_at"
        return queryset.order_by(created_field, "pk")

    if sort_by == "updated":
        updated_field = "-updated_at" if descending else "updated_at"
        return queryset.order_by(updated_field, "pk")

    # Alphabetical by task name.
    name_field = "-name" if descending else "name"
    return queryset.order_by(name_field, "pk")
