## Learned User Preferences

- Use `.env.testing` for environment templates and references; do not use `.env.example`.
- Prefer `uv` for dependency management; document both `uv` and standard venv workflows in the README.
- Export PostgreSQL credentials with `set -a && source .env.testing && set +a` before Django and test commands.
- Ensure modified files are properly commented (module docstrings and brief inline comments).
- Prefer descriptive filenames for app code (e.g., `project_create_view.py`, `project_form.py`) over generic module names.
- When asked to change schema or models only, do not add sync or business logic until explicitly requested.
- Keep new implementations minimal unless the user expands scope.

## Learned Workspace Facts

- Django take-home task manager: `config` project wrapper plus a `tasks` app.
- Stack: Django 5.x, PostgreSQL (`psycopg`), Tailwind via Play CDN (no Tailwind build step yet).
- Run Django with `uv run python manage.py`; README also documents a standard venv path.
- PostgreSQL connection uses `POSTGRES_*` env vars; defaults live in `.env.testing`.
- Database schema is documented in `docs/schema.md` and should stay in sync with `tasks/models.py`.
- Views live in `tasks/views/`; forms live in `tasks/forms/` (package layout, not monolithic files).
- `tasks/templates/home.html` is standalone and does not extend `base.html`.
- Commit Django migrations under `tasks/migrations/`; do not gitignore them.
- `setup.sh` handles cross-distro PostgreSQL setup and reloads `.env.testing` at the end.
- Single-user app per requirements (no user accounts or auth UI).
- Tests use pytest in `tests/`; `conftest.py` loads `.env.testing` when vars are not exported.
