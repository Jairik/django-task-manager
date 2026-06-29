"""Shared pytest configuration for the test suite."""

import os
from pathlib import Path


def _load_env_testing() -> None:
    """Load PostgreSQL credentials from .env.testing when not already set."""
    env_file = Path(__file__).resolve().parent.parent / ".env.testing"

    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        # Skip blank lines and comments.
        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")
        if not separator:
            continue

        # Keep values already exported in the shell.
        os.environ.setdefault(key.strip(), value.strip())


# Load env vars before Django settings are imported by pytest-django.
_load_env_testing()
