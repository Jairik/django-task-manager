# tests

Pytest suite (145 tests). `conftest.py` loads `.env.testing` when PostgreSQL env vars are missing. Coverage includes views, queries, filters, fuzzy search, and UI helpers.

```bash
set -a && source .env.testing && set +a
uv run pytest
```
