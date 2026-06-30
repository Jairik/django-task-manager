# Database schema

Reference for the PostgreSQL schema behind the task manager. Source of truth in code: `tasks/models.py` and `tasks/migrations/`. Keep this file in sync when models change.

**Database:** PostgreSQL ([stack.md](./stack.md)) · **Django app:** `tasks`

---

## Overview


| Table     | Purpose                                       |
| --------- | --------------------------------------------- |
| `project` | Top-level container for related work items    |
| `task`    | Individual work item belonging to one project |


One project has many tasks. Each task belongs to exactly one project.

```mermaid
erDiagram
    project ||--o{ task : contains

    project {
        bigint id PK
        varchar name
        date due_date
        date soonest_due_date
        varchar priority
        text description
        varchar_array tags
    }

    task {
        bigint id PK
        bigint project_id FK
        varchar name
        text description
        varchar priority
        date due_date
        varchar status
        varchar_array tags
    }
```



---

## Enums

Defined as Django `TextChoices` in `tasks/models.py`.

### Priority (`priority`)


| Value       | Label     | Notes   |
| ----------- | --------- | ------- |
| `very_low`  | Very low  |         |
| `low`       | Low       | Default |
| `medium`    | Medium    |         |
| `high`      | High      |         |
| `very_high` | Very high |         |


### Task status (`status`)


| Value         | Label       | Notes   |
| ------------- | ----------- | ------- |
| `todo`        | To do       | Default |
| `in_progress` | In progress |         |
| `done`        | Done        |         |
| `cancelled`   | Cancelled   |         |


### Tags (`tags`)

Optional list of up to **3** short labels on both `project` and `task`.


| Property   | Value                              |
| ---------- | ---------------------------------- |
| Type       | `VARCHAR(50)[]` (PostgreSQL array) |
| Max length | 3 elements                         |
| Empty      | `{}` or `NULL` — both mean no tags |


---

## `project`


| Column        | Type            | Constraints              |
| ------------- | --------------- | ------------------------ |
| `id`          | `BIGSERIAL`     | PK                       |
| `name`        | `VARCHAR(255)`  | NOT NULL                 |
| `due_date`          | `DATE`          | NULL allowed             |
| `soonest_due_date`  | `DATE`          | NULL allowed             |
| `priority`          | `VARCHAR(20)`   | NOT NULL, default `low`  |
| `description` | `TEXT`          | NULL allowed; app forms cap at 5,000 characters |
| `tags`        | `VARCHAR(50)[]` | Max 3 elements           |
| `created_at`  | `TIMESTAMPTZ`   | NOT NULL, auto on insert |
| `updated_at`  | `TIMESTAMPTZ`   | NOT NULL, auto on update |



| Index                  | Columns    | Type   | Purpose              |
| ---------------------- | ---------- | ------ | -------------------- |
| `project_due_date_idx`         | `due_date`         | B-tree | Due-date list filter              |
| `project_soonest_due_date_idx` | `soonest_due_date` | B-tree | Sort/filter by nearest task deadline |
| `project_tags_gin_idx`         | `tags`             | GIN    | Tag array storage / lookup        |
| `project_name_trgm_idx`        | `name`             | GIN (`gin_trgm_ops`) | Fuzzy name search     |
| `project_description_trgm_idx` | `description`      | GIN (`gin_trgm_ops`) | Fuzzy description search |


---

## `task`


| Column       | Type            | Constraints                 |
| ------------ | --------------- | --------------------------- |
| `id`         | `BIGSERIAL`     | PK                          |
| `project_id` | `BIGINT`        | NOT NULL, FK → `project.id` |
| `name`       | `VARCHAR(255)`  | NOT NULL                    |
| `description` | `TEXT`          | NULL allowed; app forms cap at 5,000 characters |
| `priority`   | `VARCHAR(20)`   | NOT NULL, default `low`     |
| `due_date`   | `DATE`          | NULL allowed                |
| `status`     | `VARCHAR(20)`   | NOT NULL, default `todo`    |
| `tags`       | `VARCHAR(50)[]` | Max 3 elements              |
| `created_at` | `TIMESTAMPTZ`   | NOT NULL, auto on insert    |
| `updated_at` | `TIMESTAMPTZ`   | NOT NULL, auto on update    |



| Column       | References    | On delete |
| ------------ | ------------- | --------- |
| `project_id` | `project(id)` | `CASCADE` |



| Index                 | Columns      | Type   | Purpose               |
| --------------------- | ------------ | ------ | --------------------- |
| *(FK auto-index)*     | `project_id` | B-tree | Tasks for one project (created by Django on `project` FK) |
| `task_due_date_idx`   | `due_date`   | B-tree | Task due-date queries   |
| `task_tags_gin_idx`   | `tags`       | GIN    | Tag array storage / lookup |
| `task_name_trgm_idx`        | `name`        | GIN (`gin_trgm_ops`) | Fuzzy name search        |
| `task_description_trgm_idx` | `description` | GIN (`gin_trgm_ops`) | Fuzzy description search |


### `soonest_due_date` (project)

Denormalized copy of the earliest `due_date` among **open** tasks (status `todo` or `in_progress`) with a non-null due date. Distinct from `Project.due_date`, which is the project-level deadline set on the project form.

Eligibility rules live in `tasks/queries/soonest_eligible.py` and are shared by the write refresh and the home-page `soonest_task` name subquery.

| Property | Value |
| -------- | ----- |
| Type     | `DATE` |
| Empty    | `NULL` when the project has no open dated tasks |

#### Does adding a task update `soonest_due_date`?

**Yes**, when the task goes through the app's write helpers in `tasks/queries/project_tasks.py` — not via Django signals or DB triggers.

- `create_task_for_project` saves the task, then calls `refresh_project_soonest_due_date`.
- The same refresh runs on task edit (`update_task_for_project`), delete (`delete_task_for_project`), and status-only moves (`advance_task_status`, `reopen_task_to_todo`).
- **Bypassing** those helpers (e.g. `Task.objects.create(...)` in the shell or raw tests) does **not** update the field; call `refresh_project_soonest_due_date(project)` manually if needed.

#### Where is it used?

- **Home page only** — the "Soonest" callout in `tasks/templates/home.html` shows the denormalized date next to the live-annotated task name (`soonest_task` from `get_home_projects`). Project detail does not display this field.
- Home-page **filter and sort** use the project's own `due_date` field (not `soonest_due_date`). See `tasks/queries/project_list_filters.py` and `tasks/project_list_ui.py`.

#### What does "soonest" mean?

- Earliest `due_date` among tasks with status **todo** or **in_progress** and a non-null `due_date`.
- `NULL` when no open dated tasks exist (done, cancelled, and undated tasks are ignored).

---

## PostgreSQL extensions

| Extension | Purpose |
| --------- | ------- |
| `pg_trgm` | Trigram similarity for fuzzy name/description search (`TrigramExtension` migration) |

---

## Django mapping

```python
class Priority(models.TextChoices):
    VERY_LOW = "very_low", "Very low"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very high"


class TaskStatus(models.TextChoices):
    TODO = "todo", "To do"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"
    CANCELLED = "cancelled", "Cancelled"


class Project(models.Model):
    name = models.CharField(max_length=255)
    due_date = models.DateField(null=True, blank=True)
    soonest_due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.LOW)
    description = models.TextField(blank=True)
    tags = ArrayField(models.CharField(max_length=50), size=3, default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["due_date"], name="project_due_date_idx"),
            models.Index(fields=["soonest_due_date"], name="project_soonest_due_date_idx"),
            GinIndex(fields=["tags"], name="project_tags_gin_idx"),
            GinIndex(fields=["name"], name="project_name_trgm_idx", opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["description"], name="project_description_trgm_idx", opclasses=["gin_trgm_ops"]),
        ]


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.LOW)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.TODO)
    tags = ArrayField(models.CharField(max_length=50), size=3, default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["due_date"], name="task_due_date_idx"),
            GinIndex(fields=["tags"], name="task_tags_gin_idx"),
            GinIndex(fields=["name"], name="task_name_trgm_idx", opclasses=["gin_trgm_ops"]),
            GinIndex(fields=["description"], name="task_description_trgm_idx", opclasses=["gin_trgm_ops"]),
        ]
```

