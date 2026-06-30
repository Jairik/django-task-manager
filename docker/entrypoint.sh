#!/usr/bin/env bash
# Wait for PostgreSQL, apply migrations, then exec the manage.py command from CMD.
set -euo pipefail

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-task_manager}"

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Applying database migrations..."
uv run python manage.py migrate --noinput

echo "Starting: manage.py $*"
exec uv run python manage.py "$@"
