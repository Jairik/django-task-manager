"""Landing page view."""

from django.shortcuts import render

from tasks.limits import normalize_search_query
from tasks.queries import get_home_projects


def home(request):
    """Render the home page with searchable, annotated project cards."""
    search = normalize_search_query(request.GET.get("q", ""))
    projects = get_home_projects(search=search)

    return render(
        request,
        "home.html",
        {
            "projects": projects,
        },
    )
