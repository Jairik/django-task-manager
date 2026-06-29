"""View for creating a new project."""

from django.shortcuts import redirect, render

from tasks.forms import ProjectForm


def project_create(request):
    """Show the create form (GET) or save a new project (POST)."""
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save()
            # Land on the new project's detail page so its tasks can be added.
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm()

    return render(
        request,
        "projects/project_create_form.html",
        {
            "form": form,
            "submit_label": "Create project",
        },
    )
