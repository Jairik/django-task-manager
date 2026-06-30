"""Landing page view."""

from django.shortcuts import render

from tasks.project_list_ui import (
    DUE_FILTER_CHOICES,
    FILTERABLE_PRIORITIES,
    SORT_CHOICES,
    parse_project_list_params,
)
from tasks.queries import get_home_projects, project_list_filters_from_ui_state


def home(request):
    """Render the home page with searchable, filterable project cards."""
    project_list_ui = parse_project_list_params(request.GET)
    filters = project_list_filters_from_ui_state(project_list_ui)
    projects = get_home_projects(search=project_list_ui.search, filters=filters)

    return render(
        request,
        "home.html",
        {
            "projects": projects,
            "project_list_ui": project_list_ui,
            "project_filter_priorities": FILTERABLE_PRIORITIES,
            "project_due_filter_choices": DUE_FILTER_CHOICES,
            "project_sort_choices": SORT_CHOICES,
        },
    )
