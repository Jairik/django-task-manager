"""Tests for the project detail view and task grouping queryset."""

from datetime import date

import pytest
from django.test import Client

from tasks.models import Priority, Project, Task, TaskStatus
from tasks.queries import (
    advance_task_status,
    build_task_status_sections,
    cancel_task,
    create_task_for_project,
    delete_task_for_project,
    get_next_task_status,
    get_project_tasks,
    partition_overdue_tasks,
    update_task_for_project,
)

# Fixed "today" for deterministic overdue partition unit tests.
TEST_TODAY = date(2026, 6, 15)


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
    # The design renders due dates in the compact "M j" format.
    assert "Jul 1" in content
    assert "ops" in content


@pytest.mark.django_db
def test_project_detail_empty_state(client: Client) -> None:
    """A project with no tasks shows the empty state instead of status sections.

    The design hides empty status groups, so an empty project surfaces a
    friendly "no tasks" call to action rather than the four section labels.
    """
    project = Project.objects.create(name="Empty board")

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "No tasks yet" in content


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
        "In progress",
        "To do",
        "Done",
        "Cancelled",
    ]
    assert [task.name for task in sections[1]["tasks"]] == ["Todo one"]
    assert [task.name for task in sections[2]["tasks"]] == ["Done one"]
    assert sections[0]["tasks"] == []
    assert sections[3]["tasks"] == []


@pytest.mark.django_db
def test_partition_overdue_tasks_todo_past_due() -> None:
    """Past-due todo tasks land in overdue only, not in the todo section."""
    project = Project.objects.create(name="Overdue todo")
    overdue_task = Task.objects.create(
        project=project,
        name="Late todo",
        status=TaskStatus.TODO,
        due_date=date(2026, 6, 1),
    )

    overdue_tasks, remaining_tasks = partition_overdue_tasks(
        [overdue_task],
        today=TEST_TODAY,
    )
    sections = build_task_status_sections(remaining_tasks)

    assert [task.pk for task in overdue_tasks] == [overdue_task.pk]
    assert sections[0]["tasks"] == []


@pytest.mark.django_db
def test_partition_overdue_tasks_in_progress_past_due() -> None:
    """Past-due in-progress tasks land in overdue only."""
    project = Project.objects.create(name="Overdue in progress")
    overdue_task = Task.objects.create(
        project=project,
        name="Late work",
        status=TaskStatus.IN_PROGRESS,
        due_date=date(2026, 5, 20),
    )

    overdue_tasks, remaining_tasks = partition_overdue_tasks(
        [overdue_task],
        today=TEST_TODAY,
    )
    sections = build_task_status_sections(remaining_tasks)

    assert [task.pk for task in overdue_tasks] == [overdue_task.pk]
    assert sections[1]["tasks"] == []


@pytest.mark.django_db
def test_partition_overdue_tasks_due_today_not_overdue() -> None:
    """Tasks due on the reference day stay in their status section."""
    project = Project.objects.create(name="Due today")
    on_time_task = Task.objects.create(
        project=project,
        name="Due today task",
        status=TaskStatus.TODO,
        due_date=TEST_TODAY,
    )

    overdue_tasks, remaining_tasks = partition_overdue_tasks(
        [on_time_task],
        today=TEST_TODAY,
    )
    sections = build_task_status_sections(remaining_tasks)

    assert overdue_tasks == []
    assert [task.name for task in sections[1]["tasks"]] == ["Due today task"]


@pytest.mark.django_db
def test_partition_overdue_tasks_null_due_date_not_overdue() -> None:
    """Undated open tasks are never treated as overdue."""
    project = Project.objects.create(name="No due date")
    undated_task = Task.objects.create(
        project=project,
        name="Undated todo",
        status=TaskStatus.TODO,
    )

    overdue_tasks, remaining_tasks = partition_overdue_tasks(
        [undated_task],
        today=TEST_TODAY,
    )
    sections = build_task_status_sections(remaining_tasks)

    assert overdue_tasks == []
    assert [task.name for task in sections[1]["tasks"]] == ["Undated todo"]


@pytest.mark.django_db
def test_partition_overdue_tasks_done_past_due_stays_in_done() -> None:
    """Completed tasks with past due dates remain in the done section."""
    project = Project.objects.create(name="Done late")
    done_task = Task.objects.create(
        project=project,
        name="Finished late",
        status=TaskStatus.DONE,
        due_date=date(2026, 1, 1),
    )

    overdue_tasks, remaining_tasks = partition_overdue_tasks(
        [done_task],
        today=TEST_TODAY,
    )
    sections = build_task_status_sections(remaining_tasks)

    assert overdue_tasks == []
    assert [task.name for task in sections[2]["tasks"]] == ["Finished late"]


@pytest.mark.django_db
def test_project_detail_renders_overdue_separately(client: Client) -> None:
    """Overdue tasks render under Overdue and are not duplicated in status sections."""
    project = Project.objects.create(name="Overdue board")
    Task.objects.create(
        project=project,
        name="Late item",
        status=TaskStatus.TODO,
        due_date=date(2020, 1, 1),
    )
    Task.objects.create(
        project=project,
        name="On track item",
        status=TaskStatus.TODO,
        due_date=date(2099, 1, 1),
    )

    response = client.get(f"/projects/{project.pk}/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Overdue" in content
    assert "Late item" in content
    assert "On track item" in content
    assert content.count("Late item") == 1


@pytest.mark.django_db
def test_create_task_for_project_persists_task() -> None:
    """New tasks are saved under the given project."""
    project = Project.objects.create(name="Create path")
    task = Task(
        project=project,
        name="Wire API",
        description="Document endpoints",
        priority=Priority.HIGH,
        due_date=date(2026, 9, 1),
        tags=["backend"],
    )

    saved_task = create_task_for_project(task)

    assert saved_task.pk is not None
    assert Task.objects.filter(pk=saved_task.pk, project=project).exists()
    assert saved_task.name == "Wire API"
    assert saved_task.tags == ["backend"]


@pytest.mark.django_db
def test_create_task_for_project_sets_soonest_due_date() -> None:
    """First dated task copies its due date onto the parent project."""
    project = Project.objects.create(name="Soonest seed")
    task = Task(
        project=project,
        name="First dated",
        due_date=date(2026, 8, 15),
    )

    create_task_for_project(task)
    project.refresh_from_db()

    assert project.soonest_due_date == date(2026, 8, 15)


@pytest.mark.django_db
def test_create_task_for_project_updates_soonest_when_earlier() -> None:
    """Adding an earlier dated task lowers the project's soonest_due_date."""
    project = Project.objects.create(name="Soonest update")
    Task.objects.create(
        project=project,
        name="Later",
        due_date=date(2026, 10, 1),
    )
    project.soonest_due_date = date(2026, 10, 1)
    project.save(update_fields=["soonest_due_date"])

    earlier_task = Task(
        project=project,
        name="Earlier",
        due_date=date(2026, 7, 1),
    )
    create_task_for_project(earlier_task)
    project.refresh_from_db()

    assert project.soonest_due_date == date(2026, 7, 1)


@pytest.mark.django_db
def test_create_task_for_project_undated_leaves_soonest_unchanged() -> None:
    """Undated new tasks do not clear an existing soonest_due_date."""
    project = Project.objects.create(name="Keep soonest")
    Task.objects.create(
        project=project,
        name="Dated",
        due_date=date(2026, 10, 1),
    )
    project.soonest_due_date = date(2026, 10, 1)
    project.save(update_fields=["soonest_due_date"])

    create_task_for_project(Task(project=project, name="No date"))
    project.refresh_from_db()

    assert project.soonest_due_date == date(2026, 10, 1)


@pytest.mark.django_db
def test_task_create_view_redirects_to_project_detail(client: Client) -> None:
    """POSTing the new-task form saves the task and returns to the project board."""
    project = Project.objects.create(name="Form create")

    response = client.post(
        f"/projects/{project.pk}/tasks/new/",
        {
            "name": "Ship it",
            "description": "Final checks",
            "priority": Priority.MEDIUM,
            "due_date": "2026-11-01",
            "tag_1": "release",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == f"/projects/{project.pk}/"
    assert Task.objects.filter(project=project, name="Ship it").exists()
    project.refresh_from_db()
    assert project.soonest_due_date == date(2026, 11, 1)


@pytest.mark.django_db
def test_get_next_task_status_follows_advancement_chain() -> None:
    """Status advancement follows todo → in_progress → done, then stops."""
    assert get_next_task_status(TaskStatus.TODO) == TaskStatus.IN_PROGRESS
    assert get_next_task_status(TaskStatus.IN_PROGRESS) == TaskStatus.DONE
    assert get_next_task_status(TaskStatus.DONE) is None
    assert get_next_task_status(TaskStatus.CANCELLED) is None


@pytest.mark.django_db
def test_advance_task_status_steps_through_open_statuses() -> None:
    """Repeated advances move a task from todo to done."""
    project = Project.objects.create(name="Advance path")
    task = Task.objects.create(project=project, name="Step up", status=TaskStatus.TODO)

    advance_task_status(task)
    task.refresh_from_db()
    assert task.status == TaskStatus.IN_PROGRESS

    advance_task_status(task)
    task.refresh_from_db()
    assert task.status == TaskStatus.DONE


@pytest.mark.django_db
def test_advance_task_status_is_noop_when_done() -> None:
    """Advancing a done task leaves its status unchanged."""
    project = Project.objects.create(name="Done noop")
    task = Task.objects.create(project=project, name="Finished", status=TaskStatus.DONE)

    advance_task_status(task)
    task.refresh_from_db()

    assert task.status == TaskStatus.DONE


@pytest.mark.django_db
def test_advance_task_status_is_noop_when_cancelled() -> None:
    """Advancing a cancelled task leaves its status unchanged."""
    project = Project.objects.create(name="Cancelled noop")
    task = Task.objects.create(
        project=project,
        name="Dropped",
        status=TaskStatus.CANCELLED,
    )

    advance_task_status(task)
    task.refresh_from_db()

    assert task.status == TaskStatus.CANCELLED


@pytest.mark.parametrize(
    "initial_status",
    [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE],
)
@pytest.mark.django_db
def test_cancel_task_sets_cancelled(initial_status: TaskStatus) -> None:
    """Cancel moves open or done tasks into the cancelled state."""
    project = Project.objects.create(name="Cancel path")
    task = Task.objects.create(project=project, name="Stop", status=initial_status)

    cancel_task(task)
    task.refresh_from_db()

    assert task.status == TaskStatus.CANCELLED


@pytest.mark.django_db
def test_cancel_task_is_noop_when_already_cancelled() -> None:
    """Cancelling an already-cancelled task does not error."""
    project = Project.objects.create(name="Cancel noop")
    task = Task.objects.create(
        project=project,
        name="Already stopped",
        status=TaskStatus.CANCELLED,
    )

    cancel_task(task)
    task.refresh_from_db()

    assert task.status == TaskStatus.CANCELLED


@pytest.mark.django_db
def test_task_advance_view_redirects_and_updates_status(client: Client) -> None:
    """POSTing the advance endpoint moves the task and returns to project detail."""
    project = Project.objects.create(name="Advance view")
    task = Task.objects.create(project=project, name="Move up", status=TaskStatus.TODO)

    response = client.post(f"/projects/{project.pk}/tasks/{task.pk}/advance/")

    assert response.status_code == 302
    assert response["Location"] == f"/projects/{project.pk}/"
    task.refresh_from_db()
    assert task.status == TaskStatus.IN_PROGRESS


@pytest.mark.django_db
def test_task_cancel_view_redirects_and_cancels(client: Client) -> None:
    """POSTing the cancel endpoint marks the task cancelled and redirects back."""
    project = Project.objects.create(name="Cancel view")
    task = Task.objects.create(project=project, name="Drop it", status=TaskStatus.IN_PROGRESS)

    response = client.post(f"/projects/{project.pk}/tasks/{task.pk}/cancel/")

    assert response.status_code == 302
    assert response["Location"] == f"/projects/{project.pk}/"
    task.refresh_from_db()
    assert task.status == TaskStatus.CANCELLED


@pytest.mark.django_db
def test_task_advance_view_returns_404_for_wrong_project(client: Client) -> None:
    """Advance rejects tasks that do not belong to the URL project."""
    project_a = Project.objects.create(name="Project A")
    project_b = Project.objects.create(name="Project B")
    task = Task.objects.create(project=project_a, name="Wrong board", status=TaskStatus.TODO)

    response = client.post(f"/projects/{project_b.pk}/tasks/{task.pk}/advance/")

    assert response.status_code == 404
    task.refresh_from_db()
    assert task.status == TaskStatus.TODO


@pytest.mark.django_db
def test_task_advance_view_rejects_get(client: Client) -> None:
    """GET requests to the advance endpoint are not allowed."""
    project = Project.objects.create(name="GET guard")
    task = Task.objects.create(project=project, name="No GET", status=TaskStatus.TODO)

    response = client.get(f"/projects/{project.pk}/tasks/{task.pk}/advance/")

    assert response.status_code == 405
    task.refresh_from_db()
    assert task.status == TaskStatus.TODO


@pytest.mark.django_db
def test_update_task_for_project_refreshes_soonest_due_date() -> None:
    """Editing a task's due date updates the parent project's soonest_due_date."""
    project = Project.objects.create(name="Update soonest")
    task = Task.objects.create(
        project=project,
        name="Original",
        due_date=date(2026, 10, 1),
    )
    project.soonest_due_date = date(2026, 10, 1)
    project.save(update_fields=["soonest_due_date"])

    task.due_date = date(2026, 7, 1)
    update_task_for_project(task)
    project.refresh_from_db()

    assert project.soonest_due_date == date(2026, 7, 1)


@pytest.mark.django_db
def test_delete_task_for_project_removes_task_and_refreshes_soonest() -> None:
    """Deleting the only dated task clears the project's soonest_due_date."""
    project = Project.objects.create(name="Delete soonest")
    task = Task.objects.create(
        project=project,
        name="Only dated",
        due_date=date(2026, 9, 1),
    )
    project.soonest_due_date = date(2026, 9, 1)
    project.save(update_fields=["soonest_due_date"])

    delete_task_for_project(task)
    project.refresh_from_db()

    assert not Task.objects.filter(pk=task.pk).exists()
    assert project.soonest_due_date is None


@pytest.mark.django_db
def test_task_edit_view_saves_changes(client: Client) -> None:
    """POSTing the edit form updates the task and returns to project detail."""
    project = Project.objects.create(name="Edit save")
    task = Task.objects.create(
        project=project,
        name="Before",
        status=TaskStatus.TODO,
        priority=Priority.LOW,
    )

    response = client.post(
        f"/projects/{project.pk}/tasks/{task.pk}/edit/",
        {
            "name": "After",
            "description": "Updated body",
            "priority": Priority.HIGH,
            "due_date": "2026-12-01",
            "status": TaskStatus.IN_PROGRESS,
            "tag_1": "edited",
        },
    )

    assert response.status_code == 302
    assert response["Location"] == f"/projects/{project.pk}/"
    task.refresh_from_db()
    assert task.name == "After"
    assert task.description == "Updated body"
    assert task.priority == Priority.HIGH
    assert task.due_date == date(2026, 12, 1)
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.tags == ["edited"]


@pytest.mark.django_db
def test_task_edit_view_rejects_invalid_data(client: Client) -> None:
    """Invalid edit submissions re-render the form with errors."""
    project = Project.objects.create(name="Edit invalid")
    task = Task.objects.create(project=project, name="Keep name", status=TaskStatus.TODO)

    response = client.post(
        f"/projects/{project.pk}/tasks/{task.pk}/edit/",
        {
            "name": "",
            "description": "",
            "priority": Priority.LOW,
            "status": TaskStatus.TODO,
        },
    )

    assert response.status_code == 200
    task.refresh_from_db()
    assert task.name == "Keep name"


@pytest.mark.django_db
def test_task_delete_view_removes_task(client: Client) -> None:
    """POSTing the delete endpoint removes the task and redirects back."""
    project = Project.objects.create(name="Delete view")
    task = Task.objects.create(
        project=project,
        name="Gone",
        due_date=date(2026, 8, 1),
    )
    project.soonest_due_date = date(2026, 8, 1)
    project.save(update_fields=["soonest_due_date"])

    response = client.post(f"/projects/{project.pk}/tasks/{task.pk}/delete/")

    assert response.status_code == 302
    assert response["Location"] == f"/projects/{project.pk}/"
    assert not Task.objects.filter(pk=task.pk).exists()
    project.refresh_from_db()
    assert project.soonest_due_date is None


@pytest.mark.django_db
def test_task_delete_view_returns_404_for_wrong_project(client: Client) -> None:
    """Delete rejects tasks that do not belong to the URL project."""
    project_a = Project.objects.create(name="Project A")
    project_b = Project.objects.create(name="Project B")
    task = Task.objects.create(project=project_a, name="Wrong board")

    response = client.post(f"/projects/{project_b.pk}/tasks/{task.pk}/delete/")

    assert response.status_code == 404
    assert Task.objects.filter(pk=task.pk).exists()
