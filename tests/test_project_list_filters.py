"""Unit tests for home-page project list queryset filters and sort."""

from datetime import date, timedelta

import pytest

from tasks.models import Priority, Project
from tasks.queries.project_list_filters import (
    ProjectListFilters,
    apply_project_list_filters,
    apply_project_list_sort,
)

TEST_TODAY = date(2026, 6, 15)  # Monday


@pytest.mark.django_db
def test_priority_filter_includes_only_selected_levels() -> None:
    """Priority filter keeps only projects matching checked priority values."""
    low_project = Project.objects.create(name="Low project", priority=Priority.LOW)
    Project.objects.create(name="High project", priority=Priority.HIGH)

    queryset = Project.objects.all()
    filters = ProjectListFilters(selected_priorities=("low",))
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert [project.pk for project in result] == [low_project.pk]


@pytest.mark.django_db
def test_due_filter_overdue() -> None:
    """Overdue filter matches projects with a past due date."""
    overdue_project = Project.objects.create(
        name="Late",
        due_date=TEST_TODAY - timedelta(days=1),
    )
    Project.objects.create(
        name="Future",
        due_date=TEST_TODAY + timedelta(days=1),
    )

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="overdue")
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert [project.pk for project in result] == [overdue_project.pk]


@pytest.mark.django_db
def test_due_filter_today() -> None:
    """Today filter matches projects due on the reference date."""
    today_project = Project.objects.create(name="Today", due_date=TEST_TODAY)
    Project.objects.create(name="Tomorrow", due_date=TEST_TODAY + timedelta(days=1))

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="today")
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert [project.pk for project in result] == [today_project.pk]


@pytest.mark.django_db
def test_due_filter_this_week() -> None:
    """This week filter spans Monday through Sunday of the reference week."""
    monday_project = Project.objects.create(name="Monday", due_date=TEST_TODAY)
    sunday_project = Project.objects.create(
        name="Sunday",
        due_date=TEST_TODAY + timedelta(days=6),
    )
    Project.objects.create(name="Next week", due_date=TEST_TODAY + timedelta(days=7))

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="this_week")
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert {project.pk for project in result} == {monday_project.pk, sunday_project.pk}


@pytest.mark.django_db
def test_due_filter_no_date() -> None:
    """No due date filter matches only undated projects."""
    undated_project = Project.objects.create(name="Undated", due_date=None)
    Project.objects.create(name="Dated", due_date=TEST_TODAY)

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="no_date")
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert [project.pk for project in result] == [undated_project.pk]


@pytest.mark.django_db
def test_due_filter_by_date_on_or_before() -> None:
    """By-date filter includes dated projects on or before the selected date."""
    cutoff = date(2026, 7, 1)
    on_cutoff = Project.objects.create(name="On cutoff", due_date=cutoff)
    before_cutoff = Project.objects.create(
        name="Before cutoff",
        due_date=cutoff - timedelta(days=5),
    )
    Project.objects.create(name="After cutoff", due_date=cutoff + timedelta(days=1))
    Project.objects.create(name="Undated", due_date=None)

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="by_date", due_on=cutoff)
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert {project.pk for project in result} == {on_cutoff.pk, before_cutoff.pk}


@pytest.mark.django_db
def test_due_filter_by_date_without_due_on_applies_no_due_constraint() -> None:
    """Invalid by_date (missing calendar date) does not narrow the queryset."""
    project = Project.objects.create(name="Any project", due_date=TEST_TODAY)

    queryset = Project.objects.all()
    filters = ProjectListFilters(due_filter="by_date", due_on=None)
    result = list(apply_project_list_filters(queryset, filters, today=TEST_TODAY))

    assert [item.pk for item in result] == [project.pk]


@pytest.mark.django_db
def test_sort_by_priority_descending() -> None:
    """Descending priority sort puts very_high before low."""
    low_project = Project.objects.create(name="Low", priority=Priority.LOW)
    high_project = Project.objects.create(name="High", priority=Priority.VERY_HIGH)

    queryset = Project.objects.all()
    filters = ProjectListFilters(sort_by="priority", sort_dir="desc")
    result = list(apply_project_list_sort(queryset, filters))

    assert [project.pk for project in result] == [high_project.pk, low_project.pk]


@pytest.mark.django_db
def test_sort_by_name_ascending() -> None:
    """Alphabetical sort orders projects by name."""
    zebra = Project.objects.create(name="Zebra")
    alpha = Project.objects.create(name="Alpha")

    queryset = Project.objects.all()
    filters = ProjectListFilters(sort_by="name", sort_dir="asc")
    result = list(apply_project_list_sort(queryset, filters))

    assert [project.pk for project in result] == [alpha.pk, zebra.pk]


@pytest.mark.django_db
def test_sort_by_updated_descending() -> None:
    """Updated sort uses auto_now timestamps."""
    first = Project.objects.create(name="First")
    second = Project.objects.create(name="Second")
    second.name = "Second touched"
    second.save(update_fields=["name", "updated_at"])

    queryset = Project.objects.all()
    filters = ProjectListFilters(sort_by="updated", sort_dir="desc")
    result = list(apply_project_list_sort(queryset, filters))

    assert [project.pk for project in result] == [second.pk, first.pk]
