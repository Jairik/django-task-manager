"""Shared eligibility rules for the home soonest callout and ``soonest_due_date``.

Both the denormalized project field (write path) and the home-page task-name
subquery (read path) import from here so "soonest" means the same thing.
"""

from django.db.models import Q

from tasks.models import TaskStatus

# Statuses that count as open work for soonest-due and overdue bucketing.
OPEN_TASK_STATUSES: tuple[TaskStatus, ...] = (
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
)


def eligible_soonest_tasks_filter() -> Q:
    """Return tasks that qualify for the soonest callout and ``soonest_due_date``.

    A task is eligible when it has a due date and is todo or in progress.
    Done and cancelled tasks are ignored even if they have an earlier date.
    """
    return (
        Q(due_date__isnull=False)
        & Q(status__in=OPEN_TASK_STATUSES)
    )
