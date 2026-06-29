"""WSGI config for traditional HTTP server deployment."""

import os

from django.core.wsgi import get_wsgi_application

# Tell Django which settings module to use when the server starts.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Entry point used by production servers (e.g. gunicorn).
application = get_wsgi_application()
