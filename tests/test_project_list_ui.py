"""Unit tests for home-page project toolbar URL param parsing."""

from datetime import date

from django.http import QueryDict

from tasks.models import Priority
from tasks.project_list_ui import parse_project_list_params


def test_parse_project_list_params_defaults() -> None:
    """Empty query uses default sort and no active filters."""
    state = parse_project_list_params({})

    assert state.search == ""
    assert state.selected_priorities == ()
    assert state.due_filter == "any"
    assert state.due_on is None
    assert state.sort_by == "updated"
    assert state.sort_dir == "desc"
    assert state.active_filter_count == 0
    assert state.filter_chips == ()
    assert state.sort_button_label == "Sort: Last updated ↓"


def test_parse_project_list_params_filter_chips_and_count() -> None:
    """Each active filter dimension becomes a chip and increments the badge count."""
    query = QueryDict("priority=low&due=overdue")
    state = parse_project_list_params(query)

    assert state.selected_priorities == ("low",)
    assert state.due_filter == "overdue"
    assert state.active_filter_count == 2
    assert len(state.filter_chips) == 2
    assert state.filter_chips[0].label == f"Priority: {Priority.LOW.label}"
    assert state.filter_chips[1].label == "Due: Overdue"


def test_parse_project_list_params_sort_label_ascending() -> None:
    """Sort button label reflects field and ascending direction."""
    query = QueryDict("sort=due_date&dir=asc")
    state = parse_project_list_params(query)

    assert state.sort_by == "due_date"
    assert state.sort_dir == "asc"
    assert state.sort_button_label == "Sort: Due date ↑"


def test_parse_project_list_params_manual_sort_falls_back_to_default() -> None:
    """Removed manual sort param falls back to default updated descending."""
    state = parse_project_list_params({"sort": "manual"})

    assert state.sort_by == "updated"
    assert state.sort_dir == "desc"


def test_parse_project_list_params_ignores_invalid_values() -> None:
    """Unknown priority, due, sort, and dir values are dropped."""
    query = QueryDict("priority=bogus&due=never&sort=bad&dir=sideways")
    state = parse_project_list_params(query)

    assert state.selected_priorities == ()
    assert state.due_filter == "any"
    assert state.sort_by == "updated"
    assert state.sort_dir == "desc"


def test_parse_project_list_params_multiple_repeated_priority_keys() -> None:
    """Checkbox GET submissions repeat the priority key for each selection."""
    query = QueryDict("priority=high&priority=low")
    state = parse_project_list_params(query)

    assert state.selected_priorities == ("high", "low")
    assert state.active_filter_count == 2


def test_parse_project_list_params_normalizes_search() -> None:
    """Search term is trimmed and collapsed to a single normalized string."""
    state = parse_project_list_params({"q": "  docs  ", "priority": "high"})

    assert state.search == "docs"
    assert state.selected_priorities == ("high",)


def test_parse_project_list_params_by_date_and_due_on() -> None:
    """By-date filter parses the calendar param and builds a chip label."""
    state = parse_project_list_params({"due": "by_date", "due_on": "2026-07-01"})

    assert state.due_filter == "by_date"
    assert state.due_on == date(2026, 7, 1)
    assert state.filter_chips[0].label == "Due: on or before Jul 1, 2026"


def test_parse_project_list_params_ignores_invalid_due_on() -> None:
    """Malformed due_on values are ignored without breaking other params."""
    state = parse_project_list_params({"due": "by_date", "due_on": "not-a-date"})

    assert state.due_filter == "by_date"
    assert state.due_on is None
    assert state.filter_chips[0].label == "Due: By date"
