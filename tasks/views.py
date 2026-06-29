"""Views for rendering task manager pages."""

from django.shortcuts import render


def home(request):
    """Render the landing page for unauthenticated visitors."""
    # home.html extends base.html and provides the initial placeholder content.
    return render(request, "home.html")
