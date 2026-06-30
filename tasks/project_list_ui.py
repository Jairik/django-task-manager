"""Parse home-page project list URL params for the project toolbar.

Reads GET query parameters and builds display state (chips, button labels).
Queryset filtering and sorting are applied in ``tasks.queries.project_list_filters``.
"""

from dataclasses import dataclass
from datetime import date
from typing import Any

from django.http import QueryDict

from tasks.limits import normalize_search_query
from tasks.models import Priority
from tasks.toolbar_ui_common import (
    FilterChip,
    build_filter_chips,
    build_params_dict,
    build_sort_button_label,
    parse_due_on_param,
    parse_priority_param,
)

# All priority levels available as filter checkboxes.
FILTERABLE_PRIORITIES: tuple[Priority, ...] = (
    Priority.VERY_HIGH,
    Priority.HIGH,
    Priority.MEDIUM,
    Priority.LOW,
    Priority.VERY_LOW,
)

# Due-date bucket options for the filter dropdown (project ``due_date`` field).
DUE_FILTER_CHOICES: tuple[tuple[str, str], ...] = (
    ("any", "Any time"),
    ("overdue", "Overdue"),
    ("today", "Due today"),
    ("this_week", "This week"),
    ("no_date", "No due date"),
    ("by_date", "By date"),
)

# Sort field options for the sort popover.
SORT_CHOICES: tuple[tuple[str, str], ...] = (
    ("updated", "Last updated"),
    ("due_date", "Due date"),
    ("priority", "Priority"),
    ("created", "Date created"),
    ("name", "Alphabetical"),
)

VALID_DUE_FILTERS = frozenset(value for value, _ in DUE_FILTER_CHOICES)
VALID_SORT_FIELDS = frozenset(value for value, _ in SORT_CHOICES)
VALID_SORT_DIRS = frozenset({"asc", "desc"})
VALID_PRIORITY_VALUES = frozenset(priority.value for priority in FILTERABLE_PRIORITIES)

# Home page default matches the prior ``-updated_at`` ordering.
DEFAULT_SORT_FIELD = "updated"
DEFAULT_SORT_DIR = "desc"
DEFAULT_DUE_FILTER = "any"

_PRIORITY_LABELS = dict(Priority.choices)
_DUE_LABELS = dict(DUE_FILTER_CHOICES)
_SORT_LABELS = dict(SORT_CHOICES)


@dataclass(frozen=True)
class ProjectListUIState:
    """Toolbar display state derived from GET parameters."""

    search: str
    selected_priorities: tuple[str, ...]
    due_filter: str
    due_on: date | None
    sort_by: str
    sort_dir: str
    active_filter_count: int
    filter_chips: tuple[FilterChip, ...]
    sort_button_label: str


def parse_project_list_params(query_params: QueryDict | dict[str, Any]) -> ProjectListUIState:
    """Parse GET parameters into toolbar UI state for the home page."""
    if isinstance(query_params, QueryDict):
        raw_search = query_params.get("q", "")
        raw_due = query_params.get("due", DEFAULT_DUE_FILTER)
        raw_due_on = query_params.get("due_on", "")
        raw_sort = query_params.get("sort", DEFAULT_SORT_FIELD)
        raw_dir = query_params.get("dir", DEFAULT_SORT_DIR)
    else:
        raw_search = str(query_params.get("q", ""))
        raw_due = str(query_params.get("due", DEFAULT_DUE_FILTER))
        raw_due_on = str(query_params.get("due_on", ""))
        raw_sort = str(query_params.get("sort", DEFAULT_SORT_FIELD))
        raw_dir = str(query_params.get("dir", DEFAULT_SORT_DIR))

    search = normalize_search_query(raw_search)
    selected_priorities = parse_priority_param(query_params, valid_values=VALID_PRIORITY_VALUES)
    due_filter = raw_due if raw_due in VALID_DUE_FILTERS else DEFAULT_DUE_FILTER
    due_on = parse_due_on_param(raw_due_on)

    # Legacy manual sort URLs fall back to the default updated-desc ordering.
    sort_by = raw_sort if raw_sort in VALID_SORT_FIELDS else DEFAULT_SORT_FIELD
    if raw_sort == "manual":
        sort_by = DEFAULT_SORT_FIELD

    sort_dir = raw_dir if raw_dir in VALID_SORT_DIRS else DEFAULT_SORT_DIR

    filter_chips = build_filter_chips(
        selected_priorities,
        due_filter,
        due_on,
        priority_labels=_PRIORITY_LABELS,
        due_labels=_DUE_LABELS,
        default_due_filter=DEFAULT_DUE_FILTER,
    )

    return ProjectListUIState(
        search=search,
        selected_priorities=selected_priorities,
        due_filter=due_filter,
        due_on=due_on,
        sort_by=sort_by,
        sort_dir=sort_dir,
        active_filter_count=len(filter_chips),
        filter_chips=filter_chips,
        sort_button_label=build_sort_button_label(
            sort_by,
            sort_dir,
            sort_labels=_SORT_LABELS,
            default_sort_field=DEFAULT_SORT_FIELD,
        ),
    )
