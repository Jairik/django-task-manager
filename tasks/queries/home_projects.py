"""Project queryset for the home page.

Uses live SQL aggregates for task counts, progress, and the soonest task name.
``Project.soonest_due_date`` is read from the model row (denormalized once task
CRUD maintains it). See docs/scalingConcerns.md for future denormalization.
"""

from django.db.models import (
    Case,
    Count,
    F,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)

from tasks.models import Project, Task, TaskStatus
from tasks.queries.fuzzy_search import apply_fuzzy_search


def _eligible_soonest_tasks_filter() -> Q:
    """Return tasks that can appear in the home page soonest callout."""
    return (
        Q(due_date__isnull=False)
        & ~Q(status__in=[TaskStatus.DONE, TaskStatus.CANCELLED])
    )


def get_home_projects(search: str = "") -> QuerySet[Project]:
    """Return projects for the home grid, optionally filtered by search term.

    Search matches project name, description (fuzzy trigram + substring), or any
    tag via partial/fuzzy array lookup. Annotates task_count, done_count,
    progress (integer percent), and soonest_task (name of earliest-due eligible
    task). Results are ordered by most recently updated first.
    """
    queryset = Project.objects.all()

    # Narrow the queryset before aggregates when the user typed a search term.
    queryset = apply_fuzzy_search(queryset, search)

    # Subquery: name of the next-due open task for each project row.
    soonest_task_subquery = Subquery(
        Task.objects.filter(
            project=OuterRef("pk"),
        )
        .filter(_eligible_soonest_tasks_filter())
        .order_by("due_date", "pk")
        .values("name")[:1]
    )

    # Count annotations first; progress references task_count in a second pass.
    queryset = queryset.annotate(
        task_count=Count("tasks", distinct=True),
        done_count=Count(
            "tasks",
            filter=Q(tasks__status=TaskStatus.DONE),
            distinct=True,
        ),
    ).annotate(
        progress=Case(
            When(task_count=0, then=Value(0)),
            default=(F("done_count") * 100) / F("task_count"),
            output_field=IntegerField(),
        ),
        soonest_task=soonest_task_subquery,
    )

    return queryset.order_by("-updated_at")
