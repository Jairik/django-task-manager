# Future improvements

What I would change or add with more time, or if this app needed to handle larger datasets and real traffic. The current implementation is appropriate for a single-user take-home; these are the next steps I would consider.

## Read performance and denormalization

The home page uses a hybrid query: `soonest_due_date` is denormalized on task writes, but `task_count`, `done_count`, `progress`, and `soonest_task` are computed live per request. That is fine at small scale; at thousands of projects it would hurt.

| Change | Why |
| --- | --- |
| Denormalize `task_count`, `done_count`, `soonest_task_name` on `Project` | Replace live `Count` and correlated subqueries with simple column reads |
| Centralize all counter/soonest updates in one write helper | Same pattern as `refresh_project_soonest_due_date` today — keeps denormalized fields consistent |
| Paginate the home project grid | Cap rows per request before running aggregates |
| Cache the home queryset or rendered HTML | Useful only if traffic spiked; overkill for a personal tool |

Heavier options if lists grew very large: window functions instead of correlated subqueries, or materialized views with periodic refresh.

## Search

Home `?q=` searches projects only — a project does not appear when only a child task matches. That was a deliberate scope choice to avoid `distinct()` joins across the task table.

With more time:

- **Cross-entity search** — join tasks on the home query (or a dedicated search endpoint) so task text surfaces parent projects
- **Full-text search** — PostgreSQL `tsvector` / `tsquery` or an external engine (Elasticsearch, Meilisearch) if fuzzy trigram search became insufficient
- **Search ranking** — weight name matches over description; expose relevance in the UI

## Project detail and task lists

Tasks for one project load in a single query and group in memory. For projects with hundreds of tasks:

- Paginate or virtualize long status columns
- Lazy-load done/cancelled sections
- Server-side filtering before grouping to reduce Python work

## Infrastructure and deployment

Docker Compose today is dev-only (`runserver`, bind mounts, no reverse proxy).

For production:

- Multi-stage image with Gunicorn (or uWSGI) behind nginx or a platform load balancer
- `DEBUG = False`, secrets from env/vault, `ALLOWED_HOSTS` and HTTPS
- Managed PostgreSQL (RDS, Cloud SQL) with connection pooling (PgBouncer)
- Separate migrate job from the web process in CI/CD

## Product and architecture

Not required by the brief, but natural extensions:

- **User accounts** — multi-tenant projects/tasks, per-user search and filters
- **REST or GraphQL API** — mobile clients or SPA frontend without full page reloads
- **Real-time updates** — WebSockets or SSE if multiple users edited the same project
- **Background work** — Celery + Redis for email reminders, due-date digests, or bulk imports
- **Tailwind build pipeline** — purge unused classes and pin a specific Tailwind version instead of the Play CDN
- **Audit log** — who changed task status and when

## Testing and observability

- Load tests on the home annotated query to find breakpoints before denormalizing
- Query logging / Django Debug Toolbar in dev; APM (Sentry, Datadog) in production
- Contract tests if an API layer were added

## Cool new features

A few aspirational and technically-interesting directions:

- **Semantic search** — Use embeddings (OpenAI, Hugging Face, etc.) or vector databases to surface projects and tasks by meaning rather than exact keyword match.
- **Picture upload** — Allow attaching images to projects or tasks, supporting screenshots, diagrams, or progress photos via file uploads/stable storage.
  
These would require UX work as well as backend changes:

- Semantic search means indexing data and reworking the search pipeline, with potential for ranking/categorization improvements or "show me similar" suggestions.
- File upload needs storage, thumbnailing, security (virus scan, permissions), and supporting the serving layer (CDN or proxy).

Both would add a modern polish to the tool, especially as lists grow or workflows become more visual.

