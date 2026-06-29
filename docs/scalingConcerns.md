# Scaling Concerns

Notes on read-path performance for the home page and related project list queries. See [schema.md](./schema.md) for the data model.

## Current approach (hybrid)

The home view uses **one annotated SQL query** per request:

| Field | Source | Notes |
| --- | --- | --- |
| `soonest_due_date` | `Project` model column | Denormalized; maintained by task write logic once task CRUD exists |
| `task_count`, `done_count`, `progress` | Live SQL aggregates | Computed on each home page load for now |
| `soonest_task` | Live `Subquery` | Name of the earliest-due eligible task |

This avoids N+1 queries (e.g. calling `project.tasks.count` per card in the template) and keeps task-count data correct before denormalization is implemented.

## When this is fine

For the expected scope of this project (single user, modest project/task counts), one annotated query is typically **milliseconds** and is the right tradeoff: simple, correct, and easy to defend in review.

Rough intuition:

- **Small** (e.g. 20 projects × 10 tasks): negligible cost
- **Medium** (hundreds of projects, dozens of tasks each): usually still acceptable with search narrowing the result set
- **Large** (thousands of projects on one unpaginated page): live aggregates and especially the `soonest_task` subquery can become noticeably slow

## What drives cost

1. **Number of projects returned** — unbounded lists scale linearly; search and pagination reduce work.
2. **Tasks per project** — filtered `Count` and `Min` scan related task rows.
3. **`soonest_task` subquery** — correlated subquery per project row; often the heaviest part of the home query.
4. **Index use** — existing indexes (`task_project_id_idx`, `task_due_date_idx`, `project_soonest_due_date_idx`) help; missing indexes on common filters would hurt at scale.

## Future optimizations (if needed)

### Denormalize more fields on `Project`

When task CRUD is in place, extend the same pattern used for `soonest_due_date`:

| Field | Maintain on task create / update / delete |
| --- | --- |
| `soonest_due_date` | Already planned |
| `soonest_task_name` (new column) | Replace live subquery on home |
| `task_count` (new column) | Replace live `Count` |
| `done_count` (new column) | Replace filtered live `Count` |

Home then becomes mostly `SELECT * FROM project WHERE … ORDER BY …` — very fast for read-heavy traffic.

Centralize updates in one service layer function so counts and soonest fields stay consistent.

### Query-level improvements (without new columns)

- **Pagination** on the project grid
- **Search before annotate** so aggregates run on fewer rows
- **Cache** the home queryset or rendered page (usually overkill for this app)

### Heavier options (likely overkill here)

- Window functions / advanced SQL instead of correlated subqueries
- Materialized views or periodic refresh

## Recommendation

1. **Now:** hybrid — read `soonest_due_date` from the model; annotate counts, progress, and `soonest_task` live.
2. **When task CRUD ships:** maintain `soonest_due_date` (and optionally `soonest_task_name`, `task_count`, `done_count`) on every task write.
3. **If the list grows large:** paginate first; denormalize counts and soonest task name second.

This progression keeps the first implementation simple while documenting a clear path if performance becomes a concern.

## Search

Both list pages expose a top search bar via GET `?q=`:

| Page | Scope | Fields matched |
| --- | --- | --- |
| Home (`/`) | All projects | `name`, `description` (substring + trigram fuzzy), `tags` (partial + fuzzy via `unnest`) |
| Project detail (`/projects/<id>/`) | All tasks in that project | `name`, `description` (substring + trigram fuzzy), `tags` (partial + fuzzy via `unnest`) |

**Tradeoff:** Home search does **not** surface a project when only a child task matches. Users open the project to search its tasks. This keeps the home bar scoped to projects and avoids `distinct()` joins across the task table.

**Indexed columns:** GIN trigram indexes (`gin_trgm_ops`) on `name` and `description` accelerate fuzzy lookups. GIN indexes on `tags` remain for array storage. Tag fuzzy matching unnests the array and uses `ILIKE` plus `similarity()` — it does not rely on the tags GIN index alone. B-tree indexes on `due_date` and `soonest_due_date` are reserved for the future due-date **Filter** UI (objectives #3), not the free-text search bar.

**Query order:** Search filters run before heavier work — home applies search before live aggregates; project detail applies search before overdue partitioning and status grouping. That keeps work proportional to the narrowed row set. Shared logic lives in `tasks/queries/fuzzy_search.py`.
