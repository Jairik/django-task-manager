"""Unit tests for project-detail task list queryset filters and sort."""

from datetime import date, timedelta

import pytest

from tasks.models import Priority, Project, Task, TaskStatus
from tasks.queries.task_list_filters import (
    TaskListFilters,
    apply_task_list_filters,
    apply_task_list_sort,
)

TEST_TODAY = date(2026, 6, 15)  # Monday


@pytest.fixture
def project() -> Project:
    """Bare project for task filter tests."""
    return Project.objects.create(name="Filter board")


@pytest.mark.django_db
def test_priority_filter_includes_only_selected_levels(project: Project) -> None:
    """Priority filter keeps only tasks matching checked priority values."""
    low_task = Task.objects.create(
        project=project, name="Low task", priority=Priority.LOW, status=TaskStatus.TODO
    )
    Task.objects.create(
        project=project, name="High task", priority=Priority.HIGH, status=TaskStatus.TODO
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(selected_priorities=("low",))
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert [task.pk for task in result] == [low_task.pk]


@pytest.mark.django_db
def test_due_filter_overdue(project: Project) -> None:
    """Overdue filter matches open tasks with a past due date."""
    overdue_task = Task.objects.create(
        project=project,
        name="Late",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY - timedelta(days=1),
    )
    Task.objects.create(
        project=project,
        name="Future",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY + timedelta(days=1),
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="overdue")
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert [task.pk for task in result] == [overdue_task.pk]


@pytest.mark.django_db
def test_due_filter_today(project: Project) -> None:
    """Today filter matches tasks due on the reference date."""
    today_task = Task.objects.create(
        project=project,
        name="Today",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY,
    )
    Task.objects.create(
        project=project,
        name="Tomorrow",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY + timedelta(days=1),
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="today")
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert [task.pk for task in result] == [today_task.pk]


@pytest.mark.django_db
def test_due_filter_this_week(project: Project) -> None:
    """This week filter spans Monday through Sunday of the reference week."""
    monday_task = Task.objects.create(
        project=project,
        name="Monday",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY,
    )
    sunday_task = Task.objects.create(
        project=project,
        name="Sunday",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY + timedelta(days=6),
    )
    Task.objects.create(
        project=project,
        name="Next week",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY + timedelta(days=7),
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="this_week")
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert {task.pk for task in result} == {monday_task.pk, sunday_task.pk}


@pytest.mark.django_db
def test_due_filter_no_date(project: Project) -> None:
    """No due date filter matches only undated tasks."""
    undated_task = Task.objects.create(
        project=project, name="Undated", status=TaskStatus.TODO, due_date=None
    )
    Task.objects.create(
        project=project,
        name="Dated",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY,
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="no_date")
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert [task.pk for task in result] == [undated_task.pk]


@pytest.mark.django_db
def test_due_filter_by_date_on_or_before(project: Project) -> None:
    """By-date filter includes dated tasks on or before the selected date."""
    cutoff = date(2026, 7, 1)
    on_cutoff = Task.objects.create(
        project=project,
        name="On cutoff",
        status=TaskStatus.TODO,
        due_date=cutoff,
    )
    before_cutoff = Task.objects.create(
        project=project,
        name="Before cutoff",
        status=TaskStatus.TODO,
        due_date=cutoff - timedelta(days=5),
    )
    Task.objects.create(
        project=project,
        name="After cutoff",
        status=TaskStatus.TODO,
        due_date=cutoff + timedelta(days=1),
    )
    Task.objects.create(
        project=project,
        name="Undated",
        status=TaskStatus.TODO,
        due_date=None,
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="by_date", due_on=cutoff)
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert {task.pk for task in result} == {on_cutoff.pk, before_cutoff.pk}


@pytest.mark.django_db
def test_due_filter_by_date_without_due_on_applies_no_due_constraint(project: Project) -> None:
    """Invalid by_date (missing calendar date) does not narrow the queryset."""
    task = Task.objects.create(
        project=project,
        name="Any task",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY,
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(due_filter="by_date", due_on=None)
    result = list(apply_task_list_filters(queryset, filters, today=TEST_TODAY))

    assert [task.pk for task in result] == [task.pk]


@pytest.mark.django_db
def test_sort_by_priority_descending(project: Project) -> None:
    """Descending priority sort puts very_high before low."""
    low_task = Task.objects.create(
        project=project, name="Low", priority=Priority.LOW, status=TaskStatus.TODO
    )
    high_task = Task.objects.create(
        project=project, name="High", priority=Priority.VERY_HIGH, status=TaskStatus.TODO
    )

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(sort_by="priority", sort_dir="desc")
    result = list(apply_task_list_sort(queryset, filters))

    assert [task.pk for task in result] == [high_task.pk, low_task.pk]


@pytest.mark.django_db
def test_sort_by_name_ascending(project: Project) -> None:
    """Alphabetical sort orders tasks by name."""
    zebra = Task.objects.create(project=project, name="Zebra", status=TaskStatus.TODO)
    alpha = Task.objects.create(project=project, name="Alpha", status=TaskStatus.TODO)

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(sort_by="name", sort_dir="asc")
    result = list(apply_task_list_sort(queryset, filters))

    assert [task.pk for task in result] == [alpha.pk, zebra.pk]


@pytest.mark.django_db
def test_sort_by_created_uses_timestamp(project: Project) -> None:
    """Created sort uses auto_now_add timestamps."""
    first = Task.objects.create(project=project, name="First", status=TaskStatus.TODO)
    second = Task.objects.create(project=project, name="Second", status=TaskStatus.TODO)

    queryset = Task.objects.filter(project=project)
    filters = TaskListFilters(sort_by="created", sort_dir="asc")
    result = list(apply_task_list_sort(queryset, filters))

    assert [task.pk for task in result] == [first.pk, second.pk]
