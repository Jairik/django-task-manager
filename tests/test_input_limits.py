"""Tests for app-layer input length limits (forms and search)."""

import pytest
from django.test import Client

from tasks.limits import MAX_DESCRIPTION_LENGTH, MAX_SEARCH_QUERY_LENGTH, normalize_search_query
from tasks.models import Project, Task


@pytest.fixture
def client() -> Client:
    """Return a Django test client."""
    return Client()


def test_normalize_search_query_truncates() -> None:
    """Overlong search strings are stripped and truncated to the max length."""
    raw = "x" * 300

    result = normalize_search_query(raw)

    assert len(result) == MAX_SEARCH_QUERY_LENGTH
    assert result == "x" * MAX_SEARCH_QUERY_LENGTH


def test_normalize_search_query_strips_whitespace() -> None:
    """Leading and trailing whitespace is removed before truncation."""
    assert normalize_search_query("  hello  ") == "hello"


@pytest.mark.django_db
def test_project_create_rejects_long_description(client: Client) -> None:
    """Project create form rejects descriptions over the app-layer cap."""
    overlong = "d" * (MAX_DESCRIPTION_LENGTH + 1)

    response = client.post(
        "/projects/new/",
        {
            "name": "Valid name",
            "priority": "low",
            "description": overlong,
        },
    )

    assert response.status_code == 200
    assert Project.objects.count() == 0
    content = response.content.decode()
    assert "Ensure this value has at most" in content or "description" in content.lower()


@pytest.mark.django_db
def test_task_create_rejects_long_description(client: Client) -> None:
    """Task create form rejects descriptions over the app-layer cap."""
    project = Project.objects.create(name="Parent project")
    overlong = "d" * (MAX_DESCRIPTION_LENGTH + 1)

    response = client.post(
        f"/projects/{project.pk}/tasks/new/",
        {
            "name": "Valid task",
            "priority": "low",
            "description": overlong,
        },
    )

    assert response.status_code == 200
    assert Task.objects.count() == 0


@pytest.mark.django_db
def test_home_search_with_long_query(client: Client) -> None:
    """Home page accepts an overlong ?q= by truncating server-side (no error)."""
    Project.objects.create(name="Find me")

    response = client.get("/", {"q": "f" * 300})

    assert response.status_code == 200


@pytest.mark.django_db
def test_project_detail_search_with_long_query(client: Client) -> None:
    """Project detail accepts an overlong ?q= by truncating server-side (no error)."""
    project = Project.objects.create(name="Alpha")
    Task.objects.create(project=project, name="Unique task name")

    response = client.get(f"/projects/{project.pk}/", {"q": "u" * 300})

    assert response.status_code == 200
