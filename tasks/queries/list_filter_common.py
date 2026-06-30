"""Shared list-filter helpers for home and project detail query modules."""

from datetime import date, timedelta

from django.db.models import Case, IntegerField, QuerySet, Value, When

from tasks.models import Priority

# Numeric rank for priority sort (lower = higher urgency).
PRIORITY_SORT_RANK: dict[str, int] = {
    Priority.VERY_HIGH: 0,
    Priority.HIGH: 1,
    Priority.MEDIUM: 2,
    Priority.LOW: 3,
    Priority.VERY_LOW: 4,
}


def week_bounds(today: date) -> tuple[date, date]:
    """Return Monday–Sunday bounds for the week containing ``today``."""
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def effective_due_filter(
    due_filter: str,
    due_on: date | None,
    *,
    default_due_filter: str,
) -> str:
    """Resolve by_date to any when no valid calendar date was provided."""
    if due_filter == "by_date" and due_on is None:
        return default_due_filter
    return due_filter


def apply_priority_sort(queryset: QuerySet, *, descending: bool) -> QuerySet:
    """Annotate priority rank and order by urgency (very_high first when descending)."""
    priority_cases = [
        When(priority=value, then=Value(rank))
        for value, rank in PRIORITY_SORT_RANK.items()
    ]
    queryset = queryset.annotate(
        priority_rank=Case(*priority_cases, default=Value(99), output_field=IntegerField())
    )
    # Lower rank = higher urgency; desc shows very_high first (ascending rank).
    priority_field = "priority_rank" if descending else "-priority_rank"
    return queryset.order_by(priority_field, "pk")
