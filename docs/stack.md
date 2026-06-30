# Technology stack

What was actually used to build this app, and why each piece was chosen.

## Summary


| Layer         | Choice                 | Version / notes                                                    |
| ------------- | ---------------------- | ------------------------------------------------------------------ |
| Language      | Python                 | 3.14+ (see `.python-version`)                                      |
| Web framework | Django                 | 5.2.x (locked in `uv.lock`)                                        |
| Database      | PostgreSQL             | Local install or `postgres:16-alpine` via Compose; `pg_trgm` for fuzzy search |
| DB adapter    | psycopg                | 3.x with binary wheels (`psycopg[binary]`)                         |
| Templates     | Django template engine | Server-rendered HTML; no SPA or HTMX                               |
| Styling       | Tailwind CSS           | Play CDN — no Node build step                                      |
| Typography    | Plus Jakarta Sans      | Google Fonts                                                       |
| Client JS     | Vanilla JavaScript     | Toolbar popovers and theme toggle only                             |
| Testing       | pytest + pytest-django | 145 tests in `tests/`                                              |
| Dependencies  | uv                     | Lock file for reproducible installs; pip path documented in README |
| Containers    | Docker Compose         | Dev-only: `web` (Django) + `db` (PostgreSQL 16)                    |
| Auth          | None                   | Single-user app per requirements                                   |


## Backend

**Django 5.2** handles routing, forms, ORM, migrations, CSRF, and template rendering. The project is split into:

- `config/` — settings, WSGI, root URL conf
- `tasks/` — models, views, forms, query layer, templates

Views are thin HTTP handlers (one file per route under `tasks/views/`). Read and write logic lives in `tasks/queries/` so views stay small and testable without hitting the database in every test.

**PostgreSQL** stores all data. Django's `django.contrib.postgres` contrib app enables:

- `ArrayField` for up to three tags per project/task
- `GinIndex` with `gin_trgm_ops` for fuzzy name/description search
- Standard B-tree indexes on foreign keys and due dates

The `pg_trgm` extension is enabled via a Django migration (`TrigramExtension`). Connection credentials come from `POSTGRES_`* environment variables (defaults in `.env.testing`).

**psycopg 3** is the PostgreSQL driver. Binary wheels avoid a local libpq compile step during setup.

## Frontend

**Django templates** render every page. Standalone HTML files (`home.html`, project detail, create/edit forms) include shared fragments from `tasks/templates/includes/` rather than extending a global `base.html`. This keeps each page self-contained while sharing theme setup and toolbar markup.

**Tailwind CSS** is loaded from the Play CDN in `theme_setup.html`. There is no `package.json`, PostCSS, or Tailwind build pipeline — utility classes are written directly in templates. `darkMode: 'class'` toggles light/dark via a `dark` class on `<html>`, persisted in `localStorage`.

**Vanilla JavaScript** handles UI that templates cannot:

- `static/js/home_toolbar.js` — home page filter/sort popovers
- `tasks/templates/includes/project_detail_toolbar.js` — project detail task toolbar
- `theme_header_toggle.html` — light/dark switch

No React, Vue, Alpine, or jQuery.

**Static assets** in `static/css/styles.css` supplement Tailwind where needed. Most visual design is Tailwind utility classes inline in templates.

## Data and search

Beyond basic CRUD, the schema includes deliberate PostgreSQL features:


| Feature                       | Implementation                                                               |
| ----------------------------- | ---------------------------------------------------------------------------- |
| Tag arrays                    | `VARCHAR(50)[]` via `ArrayField`, max 3 elements                             |
| Fuzzy search                  | `pg_trgm` similarity on name/description; tag search via `unnest` + `ILIKE`  |
| Denormalized soonest due date | `Project.soonest_due_date` refreshed on task writes for open tasks           |
| Live aggregates on home       | `Count`, `Min`, and a correlated subquery for progress and soonest task name |


Search scope: home `?q=` matches projects only; project detail `?q=` matches that project's tasks. See [futureImprovements.md](./futureImprovements.md) for what would change at scale.

## Testing and tooling

**pytest** with **pytest-django** runs the test suite. `conftest.py` loads `.env.testing` when PostgreSQL env vars are not already exported. Tests cover views, query helpers, filter parsing, fuzzy search, and toolbar UI state — not just happy-path smoke tests.

**uv** manages the virtual environment and lock file (`pyproject.toml` + `uv.lock`). A `requirements.txt` is also maintained for pip users.

**setup.sh** automates cross-distro PostgreSQL installation, database creation, dependency install, and migrations on Linux, macOS, and WSL.

**Docker Compose** provides an optional dev path when you do not want a local Python/PostgreSQL install:

- `docker-compose.yml` — `web` (Django `runserver` on port 8000) and `db` (`postgres:16-alpine` with a named volume)
- `Dockerfile` — `python:3.14-slim-bookworm`, `uv sync --frozen --no-dev`, `postgresql-client` for health checks
- `docker/entrypoint.sh` — waits for PostgreSQL, runs `migrate`, then execs `manage.py` (default: `runserver 0.0.0.0:8000`)
- Bind-mounts the repo into `/app` for hot reload; a separate `web_venv` volume keeps the image-built virtualenv

Start with `docker compose up --build` (see root `README.md`). `scripts/docker-compose.sh` wraps compose on Linux when the `docker` group is not yet active in the current shell. This is development-only — no production image, reverse proxy, or multi-stage build.

## What was intentionally not used

- User authentication or multi-tenancy
- REST/GraphQL API or frontend framework
- Celery, Redis, or background workers
- Production container deployment (Compose is dev-only; no Gunicorn/uWSGI image)
- Tailwind CLI build (CDN keeps the repo dependency-free on Node)
- Cloud hosting (designed for local dev; PostgreSQL choice keeps a clear migration path to RDS/Cloud SQL)

