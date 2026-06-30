"""Drop redundant task_project_id_idx (FK already indexes project_id)."""

from django.db import migrations


class Migration(migrations.Migration):
    """Remove duplicate B-tree index on Task.project_id."""

    dependencies = [
        ("tasks", "0005_refresh_soonest_due_date_open_tasks"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="task",
            name="task_project_id_idx",
        ),
    ]
