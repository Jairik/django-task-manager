"""Shared toolbar URL parsing helpers for home and project detail pages."""

from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urlencode

from django.http import QueryDict


@dataclass(frozen=True)
class FilterChip:
    """One removable active-filter chip shown below the toolbar."""

    label: str
    param: str
    value: str


def parse_due_on_param(raw: str) -> date | None:
    """Parse an ISO date string (YYYY-MM-DD) from GET; return None when invalid."""
    if not raw:
        return None

    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def parse_csv_values(raw: str, valid_values: frozenset[str]) -> tuple[str, ...]:
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


def parse_priority_param(
    query_params: QueryDict | dict[str, Any],
    *,
    valid_values: frozenset[str],
) -> tuple[str, ...]:
    """Collect priority values from repeated GET keys and comma-separated params.

    HTML checkboxes submit repeated keys (``priority=high&priority=low``);
    chip links use a comma-separated value (``priority=high,low``).
    """
    if isinstance(query_params, QueryDict):
        raw_parts = query_params.getlist("priority")
    else:
        raw_value = query_params.get("priority", "")
        if isinstance(raw_value, list):
            raw_parts = [str(value) for value in raw_value]
        elif raw_value:
            raw_parts = [str(raw_value)]
        else:
            raw_parts = []

    combined = ",".join(part for part in raw_parts if part)
    return parse_csv_values(combined, valid_values)


def build_query_string(params: dict[str, str]) -> str:
    """Serialize non-empty GET params for links and chip removal."""
    return urlencode(params)


def format_by_date_chip_label(due_on: date) -> str:
    """Human-readable chip text for the calendar due-date filter."""
    return f"Due: on or before {due_on.strftime('%b')} {due_on.day}, {due_on.year}"


def build_params_dict(
    search: str,
    selected_priorities: tuple[str, ...],
    due_filter: str,
    due_on: date | None,
    sort_by: str,
    sort_dir: str,
    *,
    default_due_filter: str,
    default_sort_field: str,
    default_sort_dir: str,
) -> dict[str, str]:
    """Build a flat param dict omitting defaults and empty values."""
    params: dict[str, str] = {}

    if search:
        params["q"] = search
    if selected_priorities:
        params["priority"] = ",".join(selected_priorities)
    if due_filter != default_due_filter:
        params["due"] = due_filter
    if due_filter == "by_date" and due_on is not None:
        params["due_on"] = due_on.isoformat()
    if sort_by != default_sort_field:
        params["sort"] = sort_by
    if sort_dir != default_sort_dir:
        params["dir"] = sort_dir

    return params


def build_filter_chips(
    selected_priorities: tuple[str, ...],
    due_filter: str,
    due_on: date | None,
    *,
    priority_labels: dict[str, str],
    due_labels: dict[str, str],
    default_due_filter: str,
) -> tuple[FilterChip, ...]:
    """Build chip rows for each active filter dimension."""
    chips: list[FilterChip] = []

    for priority in selected_priorities:
        chips.append(
            FilterChip(
                label=f"Priority: {priority_labels[priority]}",
                param="priority",
                value=priority,
            )
        )

    if due_filter != default_due_filter:
        if due_filter == "by_date" and due_on is not None:
            chip_label = format_by_date_chip_label(due_on)
        else:
            chip_label = f"Due: {due_labels[due_filter]}"

        chips.append(
            FilterChip(
                label=chip_label,
                param="due",
                value=due_filter,
            )
        )

    return tuple(chips)


def sort_direction_symbol(sort_dir: str) -> str:
    """Return the arrow shown on the Sort button."""
    return "↑" if sort_dir == "asc" else "↓"


def build_sort_button_label(
    sort_by: str,
    sort_dir: str,
    *,
    sort_labels: dict[str, str],
    default_sort_field: str,
) -> str:
    """Format the Sort button label, e.g. 'Sort: Due date ↑'."""
    field_label = sort_labels.get(sort_by, sort_labels[default_sort_field])
    return f"Sort: {field_label} {sort_direction_symbol(sort_dir)}"
