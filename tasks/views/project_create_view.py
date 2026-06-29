"""View for creating a new project."""

from django.shortcuts import redirect, render

from tasks.forms import ProjectForm


def project_create(request):
    """Show the create form (GET) or save a new project (POST)."""
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            form.save()
            # Replace with project detail redirect once that view exists.
            return redirect("home")
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
