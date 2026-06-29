"""Parse project-detail task list URL params for filter/sort toolbar UI.

Reads GET query parameters and builds display state (chips, button labels).
Queryset filtering and sorting are wired separately; this module is UI-only.
"""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from django.http import QueryDict

from tasks.limits import normalize_search_query
from tasks.models import Priority

# All priority levels available as filter checkboxes.
FILTERABLE_PRIORITIES: tuple[Priority, ...] = (
    Priority.VERY_HIGH,
    Priority.HIGH,
    Priority.MEDIUM,
    Priority.LOW,
    Priority.VERY_LOW,
)

# Due-date bucket options for the filter dropdown.
DUE_FILTER_CHOICES: tuple[tuple[str, str], ...] = (
    ("any", "Any time"),
    ("overdue", "Overdue"),
    ("today", "Due today"),
    ("this_week", "This week"),
    ("no_date", "No due date"),
)

# Sort field options for the sort popover.
SORT_CHOICES: tuple[tuple[str, str], ...] = (
    ("manual", "Manual order"),
    ("due_date", "Due date"),
    ("priority", "Priority"),
    ("created", "Date created"),
    ("updated", "Last updated"),
    ("name", "Alphabetical"),
)

VALID_DUE_FILTERS = frozenset(value for value, _ in DUE_FILTER_CHOICES)
VALID_SORT_FIELDS = frozenset(value for value, _ in SORT_CHOICES)
VALID_SORT_DIRS = frozenset({"asc", "desc"})
VALID_PRIORITY_VALUES = frozenset(priority.value for priority in FILTERABLE_PRIORITIES)

_DEFAULT_SORT = "due_date"
_DEFAULT_DIR = "asc"
_DEFAULT_DUE = "any"

_PRIORITY_LABELS = dict(Priority.choices)
_DUE_LABELS = dict(DUE_FILTER_CHOICES)
_SORT_LABELS = dict(SORT_CHOICES)


@dataclass(frozen=True)
class FilterChip:
    """One removable active-filter chip shown below the toolbar."""

    chip_id: str
    label: str
    param: str
    value: str


@dataclass(frozen=True)
class TaskListUIState:
    """Toolbar display state derived from GET parameters."""

    search: str
    selected_priorities: tuple[str, ...]
    due_filter: str
    sort_by: str
    sort_dir: str
    active_filter_count: int
    filter_chips: tuple[FilterChip, ...]
    sort_button_label: str
    is_manual_sort: bool
    query_string: str


def _parse_csv_values(raw: str, valid_values: frozenset[str]) -> tuple[str, ...]:
    """Split a comma-separated param and keep only recognized values."""
    if not raw:
        return ()

    seen: set[str] = set()
    ordered: list[str] = []
    for part in raw.split(","):
        value = part.strip()
        if value in valid_values and value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _build_query_string(params: dict[str, str]) -> str:
    """Serialize non-empty GET params for links and chip removal."""
    return urlencode(params)


def _build_params_dict(
    search: str,
    selected_priorities: tuple[str, ...],
    due_filter: str,
    sort_by: str,
    sort_dir: str,
) -> dict[str, str]:
    """Build a flat param dict omitting defaults and empty values."""
    params: dict[str, str] = {}

    if search:
        params["q"] = search
    if selected_priorities:
        params["priority"] = ",".join(selected_priorities)
    if due_filter != _DEFAULT_DUE:
        params["due"] = due_filter
    if sort_by != _DEFAULT_SORT:
        params["sort"] = sort_by
    if sort_dir != _DEFAULT_DIR:
        params["dir"] = sort_dir

    return params


def _build_filter_chips(
    selected_priorities: tuple[str, ...],
    due_filter: str,
) -> tuple[FilterChip, ...]:
    """Build chip rows for each active filter dimension."""
    chips: list[FilterChip] = []

    for priority in selected_priorities:
        chips.append(
            FilterChip(
                chip_id=f"priority:{priority}",
                label=f"Priority: {_PRIORITY_LABELS[priority]}",
                param="priority",
                value=priority,
            )
        )

    if due_filter != _DEFAULT_DUE:
        chips.append(
            FilterChip(
                chip_id=f"due:{due_filter}",
                label=f"Due: {_DUE_LABELS[due_filter]}",
                param="due",
                value=due_filter,
            )
        )

    return tuple(chips)


def _sort_direction_symbol(sort_dir: str) -> str:
    """Return the arrow shown on the Sort button."""
    return "↑" if sort_dir == "asc" else "↓"


def _build_sort_button_label(sort_by: str, sort_dir: str) -> str:
    """Format the Sort button label, e.g. 'Sort: Due date ↑'."""
    field_label = _SORT_LABELS.get(sort_by, _SORT_LABELS[_DEFAULT_SORT])
    return f"Sort: {field_label} {_sort_direction_symbol(sort_dir)}"


def build_task_list_query_string(
    search: str = "",
    selected_priorities: tuple[str, ...] = (),
    due_filter: str = _DEFAULT_DUE,
    sort_by: str = _DEFAULT_SORT,
    sort_dir: str = _DEFAULT_DIR,
) -> str:
    """Serialize toolbar params for navigation links."""
    params = _build_params_dict(
        search=search,
        selected_priorities=selected_priorities,
        due_filter=due_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return _build_query_string(params)


def parse_task_list_params(query_params: QueryDict | dict[str, Any]) -> TaskListUIState:
    """Parse GET parameters into toolbar UI state for the project detail page."""
    if isinstance(query_params, QueryDict):
        raw_search = query_params.get("q", "")
        raw_priority = query_params.get("priority", "")
        raw_due = query_params.get("due", _DEFAULT_DUE)
        raw_sort = query_params.get("sort", _DEFAULT_SORT)
        raw_dir = query_params.get("dir", _DEFAULT_DIR)
    else:
        raw_search = str(query_params.get("q", ""))
        raw_priority = str(query_params.get("priority", ""))
        raw_due = str(query_params.get("due", _DEFAULT_DUE))
        raw_sort = str(query_params.get("sort", _DEFAULT_SORT))
        raw_dir = str(query_params.get("dir", _DEFAULT_DIR))

    search = normalize_search_query(raw_search)
    selected_priorities = _parse_csv_values(raw_priority, VALID_PRIORITY_VALUES)
    due_filter = raw_due if raw_due in VALID_DUE_FILTERS else _DEFAULT_DUE
    sort_by = raw_sort if raw_sort in VALID_SORT_FIELDS else _DEFAULT_SORT
    sort_dir = raw_dir if raw_dir in VALID_SORT_DIRS else _DEFAULT_DIR

    filter_chips = _build_filter_chips(selected_priorities, due_filter)

    return TaskListUIState(
        search=search,
        selected_priorities=selected_priorities,
        due_filter=due_filter,
        sort_by=sort_by,
        sort_dir=sort_dir,
        active_filter_count=len(filter_chips),
        filter_chips=filter_chips,
        sort_button_label=_build_sort_button_label(sort_by, sort_dir),
        is_manual_sort=sort_by == "manual",
        query_string=build_task_list_query_string(
            search=search,
            selected_priorities=selected_priorities,
            due_filter=due_filter,
            sort_by=sort_by,
            sort_dir=sort_dir,
        ),
    )
