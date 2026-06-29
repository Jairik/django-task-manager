"""Verify the PostgreSQL database exists and accepts connections."""

import os

import psycopg


def _connection_params() -> dict[str, str]:
    """Build PostgreSQL connection kwargs from .env.testing / environment."""
    return {
        "dbname": os.environ.get("POSTGRES_DB", "task_manager"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }


def test_database_exists_and_connects():
    """Confirm the configured PostgreSQL database exists and accepts connections."""
    params = _connection_params()

    # connect() raises if the server is down, credentials are wrong, or the DB is missing.
    with psycopg.connect(**params) as conn:
        with conn.cursor() as cursor:
            # current_database() confirms we reached the expected database.
            cursor.execute("SELECT current_database()")
            active_db = cursor.fetchone()[0]

            # Simple query proves the connection is usable.
            cursor.execute("SELECT 1")
            ping_result = cursor.fetchone()[0]

    assert active_db == params["dbname"]
    assert ping_result == 1
