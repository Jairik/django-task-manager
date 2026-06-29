"""Tests for the home page view and project list queryset."""

from datetime import date

import pytest
from django.test import Client

from tasks.models import Project, Task, TaskStatus


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
        due_date=date(2026, 6, 1),
    )
    Task.objects.create(
        project=project,
        name="Deploy",
        status=TaskStatus.TODO,
        due_date=date(2026, 6, 15),
    )

    response = client.get("/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "50%" in content
    assert "1/2 tasks" in content
    assert "Deploy" in content
