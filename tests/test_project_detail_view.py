"""Tests for the project detail view and task grouping queryset."""

from datetime import date

import pytest
from django.test import Client

from tasks.models import Priority, Project, Task, TaskStatus
from tasks.queries import build_task_status_sections, get_project_tasks


@pytest.fixture
def client() -> Client:
    """Return a Django test client."""
    return Client()


@pytest.mark.django_db
def test_project_detail_404_for_missing_project(client: Client) -> None:
    """Unknown project primary key returns 404."""
    response = client.get("/projects/99999/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_project_detail_renders_project_header(client: Client) -> None:
    """Project detail page shows the project name and priority label."""
    project = Project.objects.create(name="Ship feature", priority=Priority.HIGH)

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Ship feature" in content
    assert "High" in content


@pytest.mark.django_db
def test_project_detail_groups_tasks_by_status(client: Client) -> None:
    """Tasks appear under their status section headings."""
    project = Project.objects.create(name="Release prep")
    Task.objects.create(project=project, name="Write docs", status=TaskStatus.TODO)
    Task.objects.create(project=project, name="Run QA", status=TaskStatus.IN_PROGRESS)
    Task.objects.create(project=project, name="Tag release", status=TaskStatus.DONE)

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "To do" in content
    assert "In progress" in content
    assert "Done" in content
    assert "Write docs" in content
    assert "Run QA" in content
    assert "Tag release" in content


@pytest.mark.django_db
def test_project_detail_includes_all_task_fields(client: Client) -> None:
    """Task priority, due date, description, and tags render on the page."""
    project = Project.objects.create(name="Field coverage")
    Task.objects.create(
        project=project,
        name="Audit logs",
        description="Review retention policy",
        priority=Priority.MEDIUM,
        due_date=date(2026, 7, 1),
        status=TaskStatus.TODO,
        tags=["ops"],
    )

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Audit logs" in content
    assert "Review retention policy" in content
    assert "Medium" in content
    assert "July 1, 2026" in content
    assert "ops" in content


@pytest.mark.django_db
def test_project_detail_empty_sections(client: Client) -> None:
    """Project with no tasks still shows all four status section labels."""
    project = Project.objects.create(name="Empty board")

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "To do" in content
    assert "In progress" in content
    assert "Done" in content
    assert "Cancelled" in content


@pytest.mark.django_db
def test_get_project_tasks_ordering() -> None:
    """Tasks are ordered by due date (nulls last), then name."""
    project = Project.objects.create(name="Ordering")
    later = Task.objects.create(
        project=project,
        name="Beta task",
        due_date=date(2026, 8, 1),
    )
    earlier = Task.objects.create(
        project=project,
        name="Alpha task",
        due_date=date(2026, 7, 1),
    )
    undated = Task.objects.create(project=project, name="No date task")

    task_ids = list(get_project_tasks(project.pk).values_list("pk", flat=True))

    assert task_ids == [earlier.pk, later.pk, undated.pk]


@pytest.mark.django_db
def test_build_task_status_sections_preserves_order() -> None:
    """Grouped sections follow TASK_STATUS_SECTION_ORDER regardless of input order."""
    project = Project.objects.create(name="Sections")
    done_task = Task.objects.create(project=project, name="Done one", status=TaskStatus.DONE)
    todo_task = Task.objects.create(project=project, name="Todo one", status=TaskStatus.TODO)

    sections = build_task_status_sections([done_task, todo_task])

    assert [section["label"] for section in sections] == [
        "To do",
        "In progress",
        "Done",
        "Cancelled",
    ]
    assert [task.name for task in sections[0]["tasks"]] == ["Todo one"]
    assert [task.name for task in sections[2]["tasks"]] == ["Done one"]
    assert sections[1]["tasks"] == []
    assert sections[3]["tasks"] == []
