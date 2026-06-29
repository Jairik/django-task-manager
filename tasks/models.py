"""Data models for projects and tasks (see docs/schema.md)."""

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class Priority(models.TextChoices):
    """Shared priority scale for projects and tasks."""

    VERY_LOW = "very_low", "Very low"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very high"


class TaskStatus(models.TextChoices):
    """Lifecycle state for an individual task."""

    TODO = "todo", "To do"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


class Project(models.Model):
    """Top-level container grouping related tasks."""

    name = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.LOW,
    )
    description = models.TextField(blank=True)
    # Up to three optional short labels stored as a PostgreSQL varchar array.
    tags = ArrayField(
        models.CharField(max_length=50),
        size=3,
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Meta options: adds indexes to optimize queries on due_date and tags fields for Project.
    class Meta:
        indexes = [
            models.Index(fields=["due_date"], name="project_due_date_idx"),
            GinIndex(fields=["tags"], name="project_tags_gin_idx"),
        ]
  

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    """Single work item that belongs to exactly one project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,  # delete all tasks when a project is deleted
        related_name="tasks",
    )
    name = models.CharField(max_length=255)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.LOW,  # default priority is low
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO,
    )
    tags = ArrayField(
        models.CharField(max_length=50),
        size=3,
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Meta options: adds indexes to optimize queries on project and tags fields for Task.
    class Meta:
        indexes = [
            models.Index(fields=["project"], name="task_project_id_idx"),
            GinIndex(fields=["tags"], name="task_tags_gin_idx"),
        ]

    def __str__(self) -> str:
        return self.name
