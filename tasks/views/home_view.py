"""Landing page view."""

from django.shortcuts import render

from tasks.queries import get_home_projects


def home(request):
    """Render the home page with searchable, annotated project cards."""
    search = request.GET.get("q", "").strip()
    projects = get_home_projects(search=search)

    return render(
        request,
        "home.html",
        {
            "projects": projects,
        },
    )
