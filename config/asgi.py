"""ASGI config for async-capable server deployment."""

import os

from django.core.asgi import get_asgi_application

# Tell Django which settings module to use when the server starts.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Entry point used by async servers (e.g. uvicorn, daphne).
application = get_asgi_application()
