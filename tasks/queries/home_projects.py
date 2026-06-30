"""Project queryset for the home page.

Uses live SQL aggregates for task counts, progress, and the soonest task name.
``Project.soonest_due_date`` is denormalized on task writes; ``soonest_task``
is a live subquery for the name only. Both share eligibility rules from
``soonest_eligible.py``. See docs/futureImprovements.md for denormalization at scale.
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
from tasks.queries.project_list_filters import (
    ProjectListFilters,
    apply_project_list_filters,
    apply_project_list_sort,
)
from tasks.queries.soonest_eligible import eligible_soonest_tasks_filter


def get_home_projects(
    search: str = "",
    *,
    filters: ProjectListFilters | None = None,
) -> QuerySet[Project]:
    """Return projects for the home grid with optional search, filter, and sort.

    Search matches project name, description (fuzzy trigram + substring), or any
    tag via partial/fuzzy array lookup. Annotates task_count, done_count,
    progress (integer percent), and soonest_task (name of earliest-due eligible
    task). Toolbar filters and sort run after search and before annotations.
    """
    queryset = Project.objects.all()

    # Narrow the queryset before heavier work when the user typed a search term.
    queryset = apply_fuzzy_search(queryset, search)

    if filters is not None:
        queryset = apply_project_list_filters(queryset, filters)

    # Subquery: name of the next-due open task for each project row.
    soonest_task_subquery = Subquery(
        Task.objects.filter(
            project=OuterRef("pk"),
        )
        .filter(eligible_soonest_tasks_filter())
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

    if filters is not None:
        return apply_project_list_sort(queryset, filters)

    return queryset.order_by("-updated_at")
