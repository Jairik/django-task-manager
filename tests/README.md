# Automated Tests

Pytest suite for the django-task-manager project.

## Run instructions

Load environment variables and install test dependencies first:

```bash
set -a && source .env.testing && set +a
uv sync --group dev
```

Run all tests:

```bash
uv run pytest
```

Run only the database initialization test:

```bash
uv run pytest tests/db_init.py
```

### pip + venv fallback

```bash
set -a && source .env.testing && set +a
source .venv/bin/activate
pip install -r requirements.txt pytest pytest-django
pytest
```

Note: `tests/conftest.py` loads `.env.testing` automatically when variables are not already exported, but sourcing the file yourself is still recommended before running tests.

## Test summary

| File | Test | What it checks |
|------|------|----------------|
| `db_init.py` | `test_database_exists_and_connects` | The PostgreSQL server is running, the database named in `.env.testing` exists, and a connection can be opened and queried successfully. |
