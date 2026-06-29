"""Unit tests for project-detail task toolbar URL param parsing."""

from django.http import QueryDict

from tasks.models import Priority
from tasks.task_list_ui import parse_task_list_params


def test_parse_task_list_params_defaults() -> None:
    """Empty query uses default sort and no active filters."""
    state = parse_task_list_params({})

    assert state.search == ""
    assert state.selected_priorities == ()
    assert state.due_filter == "any"
    assert state.sort_by == "due_date"
    assert state.sort_dir == "asc"
    assert state.active_filter_count == 0
    assert state.filter_chips == ()
    assert state.sort_button_label == "Sort: Due date ↑"
    assert state.is_manual_sort is False
    assert state.query_string == ""


def test_parse_task_list_params_filter_chips_and_count() -> None:
    """Each active filter dimension becomes a chip and increments the badge count."""
    query = QueryDict("priority=low&due=overdue")
    state = parse_task_list_params(query)

    assert state.selected_priorities == ("low",)
    assert state.due_filter == "overdue"
    assert state.active_filter_count == 2
    assert len(state.filter_chips) == 2
    assert state.filter_chips[0].label == f"Priority: {Priority.LOW.label}"
    assert state.filter_chips[1].label == "Due: Overdue"


def test_parse_task_list_params_sort_label_descending() -> None:
    """Sort button label reflects field and descending direction."""
    query = QueryDict("sort=priority&dir=desc")
    state = parse_task_list_params(query)

    assert state.sort_by == "priority"
    assert state.sort_dir == "desc"
    assert state.sort_button_label == "Sort: Priority ↓"
    assert state.is_manual_sort is False


def test_parse_task_list_params_manual_sort() -> None:
    """Manual sort sets the flag used for future drag reorder."""
    state = parse_task_list_params({"sort": "manual"})

    assert state.sort_by == "manual"
    assert state.is_manual_sort is True
    assert "sort=manual" in state.query_string


def test_parse_task_list_params_ignores_invalid_values() -> None:
    """Unknown priority, due, sort, and dir values are dropped."""
    query = QueryDict("priority=bogus&due=never&sort=bad&dir=sideways")
    state = parse_task_list_params(query)

    assert state.selected_priorities == ()
    assert state.due_filter == "any"
    assert state.sort_by == "due_date"
    assert state.sort_dir == "asc"


def test_parse_task_list_params_search_and_query_string() -> None:
    """Search term is normalized and included in the serialized query string."""
    state = parse_task_list_params({"q": "  docs  ", "priority": "high"})

    assert state.search == "docs"
    assert "q=docs" in state.query_string
    assert "priority=high" in state.query_string
