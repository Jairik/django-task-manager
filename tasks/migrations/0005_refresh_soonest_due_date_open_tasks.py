"""Recompute soonest_due_date using open-task-only eligibility rules."""

from django.db import migrations
from django.db.models import Min, Q


def refresh_all_project_soonest_due_dates(apps, schema_editor):
    """Backfill soonest_due_date for every project row.

    Mirrors ``refresh_project_soonest_due_date`` in project_tasks.py: earliest
    due date among todo and in-progress tasks only.
    """
    Project = apps.get_model("tasks", "Project")
    Task = apps.get_model("tasks", "Task")

    open_statuses = ("todo", "in_progress")
    eligible_filter = Q(due_date__isnull=False) & Q(status__in=open_statuses)

    for project in Project.objects.all().iterator():
        soonest_due_date = (
            Task.objects.filter(project_id=project.pk)
            .filter(eligible_filter)
            .aggregate(soonest=Min("due_date"))
            .get("soonest")
        )
        # Update only the denormalized cache so auto_now updated_at stays unchanged.
        project.soonest_due_date = soonest_due_date
        project.save(update_fields=["soonest_due_date"])


class Migration(migrations.Migration):

    dependencies = [
        ("tasks", "0004_fuzzy_search_trigram"),
    ]

    operations = [
        migrations.RunPython(
            refresh_all_project_soonest_due_dates,
            migrations.RunPython.noop,
        ),
    ]
