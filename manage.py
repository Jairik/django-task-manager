#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks using the project's settings module."""
    # Default settings location used by runserver, migrate, and other commands.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Give a clear install hint when Django is missing from the environment.
        raise ImportError(
            "Couldn't import Django. Install dependencies with: uv sync "
            "or pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
