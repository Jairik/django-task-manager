"""Tests for the home page view and project list queryset."""

from datetime import date

import pytest
from django.test import Client

from tasks.models import Priority, Project, Task, TaskStatus
from tasks.queries import refresh_project_soonest_due_date


@pytest.fixture
def client() -> Client:
    """Return a Django test client."""
    return Client()


@pytest.mark.django_db
def test_home_lists_projects(client: Client) -> None:
    """Home page renders all projects when no search term is provided."""
    Project.objects.create(name="Alpha Release")
    Project.objects.create(name="Beta Cleanup")

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Alpha Release" in content
    assert "Beta Cleanup" in content


@pytest.mark.django_db
def test_home_search_by_name(client: Client) -> None:
    """Search filters projects by partial name match."""
    Project.objects.create(name="Alpha Release")
    Project.objects.create(name="Beta Cleanup")

    response = client.get("/", {"q": "alpha"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Alpha Release" in content
    assert "Beta Cleanup" not in content


@pytest.mark.django_db
def test_home_search_by_tag(client: Client) -> None:
    """Search matches tags by partial and exact text."""
    # Name deliberately avoids "backend" so a partial tag query cannot match via name.
    Project.objects.create(name="API refactor", tags=["backend"])
    Project.objects.create(name="UI polish", tags=["frontend"])

    exact_match = client.get("/", {"q": "backend"})
    partial_match = client.get("/", {"q": "back"})

    exact_content = exact_match.content.decode()
    partial_content = partial_match.content.decode()

    assert "API refactor" in exact_content
    assert "UI polish" not in exact_content
    assert "API refactor" in partial_content
    assert "UI polish" not in partial_content


@pytest.mark.django_db
def test_home_search_fuzzy_name_typo(client: Client) -> None:
    """Fuzzy search tolerates minor typos in project names."""
    Project.objects.create(name="Alpha Release")
    Project.objects.create(name="Beta Cleanup")

    response = client.get("/", {"q": "Alpa Release"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Alpha Release" in content
    assert "Beta Cleanup" not in content


@pytest.mark.django_db
def test_home_search_by_description(client: Client) -> None:
    """Search filters projects by partial description match."""
    Project.objects.create(name="Alpha", description="Quarterly roadmap planning")
    Project.objects.create(name="Beta", description="Unrelated cleanup work")

    response = client.get("/", {"q": "roadmap"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "Alpha" in content
    assert "Beta" not in content


@pytest.mark.django_db
def test_home_annotations(client: Client) -> None:
    """Home page shows progress, task counts, and soonest task from annotations."""
    project = Project.objects.create(name="Ship feature")
    Task.objects.create(
        project=project,
        name="Write tests",
        status=TaskStatus.DONE,
        due_date=date(2026, 5, 1),
    )
    Task.objects.create(
        project=project,
        name="Deploy",
        status=TaskStatus.TODO,
        due_date=date(2026, 6, 15),
    )
    refresh_project_soonest_due_date(project)

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "50%" in content
    assert "1/2 tasks" in content
    assert "Deploy" in content
    assert "Jun 15" in content
    assert "May 1" not in content


@pytest.mark.django_db
def test_home_filter_by_priority(client: Client) -> None:
    """Priority filter hides projects that do not match the selected level."""
    Project.objects.create(name="Low only", priority=Priority.LOW)
    Project.objects.create(name="High other", priority=Priority.HIGH)

    response = client.get("/?priority=low")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Low only" in content
    assert "High other" not in content


@pytest.mark.django_db
def test_home_filter_by_overdue(client: Client) -> None:
    """Overdue due filter shows only projects past their due date."""
    Project.objects.create(name="Late project", due_date=date(2020, 1, 1))
    Project.objects.create(name="Future project", due_date=date(2099, 1, 1))

    response = client.get("/?due=overdue")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Late project" in content
    assert "Future project" not in content


@pytest.mark.django_db
def test_home_filter_by_date_on_or_before(client: Client) -> None:
    """By-date filter shows dated projects due on or before the selected date."""
    Project.objects.create(name="Before cutoff", due_date=date(2026, 6, 20))
    Project.objects.create(name="On cutoff", due_date=date(2026, 7, 1))
    Project.objects.create(name="After cutoff", due_date=date(2026, 7, 15))
    Project.objects.create(name="Undated project", due_date=None)

    response = client.get("/?due=by_date&due_on=2026-07-01")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Before cutoff" in content
    assert "On cutoff" in content
    assert "After cutoff" not in content
    assert "Undated project" not in content


@pytest.mark.django_db
def test_home_sort_by_priority_desc(client: Client) -> None:
    """Priority descending sort renders higher urgency projects first."""
    Project.objects.create(name="Low project", priority=Priority.LOW)
    Project.objects.create(name="High project", priority=Priority.VERY_HIGH)

    response = client.get("/?sort=priority&dir=desc")

    assert response.status_code == 200
    content = response.content.decode()
    assert content.index("High project") < content.index("Low project")


@pytest.mark.django_db
def test_home_toolbar_by_date_input(client: Client) -> None:
    """By-date filter renders the calendar input with the selected value."""
    response = client.get("/?due=by_date&due_on=2026-07-01")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="project-due-on-input"' in content
    assert 'value="2026-07-01"' in content
    assert "Due: on or before Jul 1, 2026" in content


@pytest.mark.django_db
def test_home_toolbar_default_labels(client: Client) -> None:
    """Default toolbar shows Filter and Sort labels without an active filter badge."""
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'id="project-filter-trigger"' in content
    assert 'id="project-sort-trigger"' in content
    assert "Filter projects" in content
    assert "Sort: Last updated ↓" in content


@pytest.mark.django_db
def test_home_toolbar_active_filter_chips(client: Client) -> None:
    """Active filter URL params render chips and a Filter count badge."""
    response = client.get("/?priority=low")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Priority: Low" in content
    assert 'data-chip-param="priority"' in content
    assert 'aria-label="Filter projects (1 active)"' in content


@pytest.mark.django_db
def test_home_toolbar_sort_button_label(client: Client) -> None:
    """Sort button label reflects sort field and descending direction from the URL."""
    response = client.get("/?sort=priority&dir=desc")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Sort: Priority ↓" in content
    assert 'value="priority"' in content
    assert 'value="desc"' in content


@pytest.mark.django_db
def test_home_toolbar_script_is_executable(client: Client) -> None:
    """Home toolbar JavaScript is loaded via a deferred script tag."""
    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert 'src="/static/js/list_toolbar.js"' in content
    assert 'defer' in content


@pytest.mark.django_db
def test_home_sort_manual_falls_back_to_default(client: Client) -> None:
    """Bookmarked manual sort URLs fall back to default updated sort."""
    Project.objects.create(name="Any project")

    response = client.get("/?sort=manual")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Sort: Last updated ↓" in content
