"""Landing page view."""

from django.shortcuts import render


def home(request):
    """Render the site landing page."""
    return render(request, "home.html")
