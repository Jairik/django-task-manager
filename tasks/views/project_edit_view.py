"""View for editing an existing project."""

from django.shortcuts import get_object_or_404, redirect, render

from tasks.forms import ProjectForm
from tasks.models import Project


def project_edit(request, pk: int):
    """Show the edit-project form (GET) or save changes (POST)."""
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    return render(
        request,
        "projects/project_edit_form.html",
        {
            "project": project,
            "form": form,
            "submit_label": "Save changes",
        },
    )
